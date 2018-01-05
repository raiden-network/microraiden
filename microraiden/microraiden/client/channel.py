import logging
from enum import Enum

from eth_utils import decode_hex, is_same_address
from typing import Callable

from microraiden.client.context import Context
from microraiden.utils import (
    get_event_blocking,
    create_signed_contract_transaction,
    sign_balance_proof,
    verify_closing_sig,
    keccak256
)

log = logging.getLogger(__name__)


class Channel:
    class State(Enum):
        open = 1
        settling = 2
        closed = 3

    def __init__(
            self,
            core: Context,
            sender: str,
            receiver: str,
            block: int,
            deposit: int = 0,
            balance: int = 0,
            state: State = State.open,
            on_settle: Callable[['Channel'], None] = lambda channel: None
    ):
        self._balance = 0
        self._balance_sig = None

        self.core = core
        self.sender = sender
        self.receiver = receiver
        self.deposit = deposit
        self.block = block
        self.update_balance(balance)
        self.state = state
        self.on_settle = on_settle

        assert self.block is not None
        assert self._balance_sig

    @property
    def balance(self):
        return self._balance

    @property
    def key(self) -> bytes:
        return keccak256(self.sender, self.receiver, self.block)

    def update_balance(self, value):
        self._balance = value
        self._balance_sig = self.sign()

    @property
    def balance_sig(self):
        return self._balance_sig

    def sign(self):
        return sign_balance_proof(
            self.core.private_key,
            self.receiver,
            self.block,
            self.balance,
            self.core.channel_manager.address
        )

    def topup(self, deposit):
        """
        Attempts to increase the deposit in an existing channel. Block until confirmation.
        """
        if self.state != Channel.State.open:
            log.error('Channel must be open to be topped up.')
            return

        token_balance = self.core.token.call().balanceOf(self.core.address)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified topup ({}/{})'
                .format(token_balance, deposit)
            )
            return None

        log.info('Topping up channel to {} created at block #{} by {} tokens.'.format(
            self.receiver, self.block, deposit
        ))
        current_block = self.core.web3.eth.blockNumber

        data = (decode_hex(self.sender) +
                decode_hex(self.receiver) +
                self.block.to_bytes(4, byteorder='big'))
        tx = create_signed_contract_transaction(
            self.core.private_key,
            self.core.token,
            'transfer',
            [
                self.core.channel_manager.address,
                deposit,
                data
            ]
        )
        self.core.web3.eth.sendRawTransaction(tx)

        log.debug('Waiting for topup confirmation event...')
        event = get_event_blocking(
            self.core.channel_manager,
            'ChannelToppedUp',
            from_block=current_block + 1,
            argument_filters={
                '_sender_address': self.sender,
                '_receiver_address': self.receiver,
                '_open_block_number': self.block
            }
        )

        if event:
            log.debug('Successfully topped up channel in block {}.'.format(event['blockNumber']))
            self.deposit += deposit
            return event
        else:
            log.error('No event received.')
            return None

    def close(self, balance=None):
        """
        Attempts to request close on a channel. An explicit balance can be given to override the
        locally stored balance signature. Blocks until a confirmation event is received or timeout.
        """
        if self.state != Channel.State.open:
            log.error('Channel must be open to request a close.')
            return
        log.info('Requesting close of channel to {} created at block #{}.'.format(
            self.receiver, self.block
        ))
        current_block = self.core.web3.eth.blockNumber

        if balance is not None:
            self.update_balance(balance)

        tx = create_signed_contract_transaction(
            self.core.private_key,
            self.core.channel_manager,
            'uncooperativeClose',
            [
                self.receiver,
                self.block,
                self.balance
            ]
        )
        self.core.web3.eth.sendRawTransaction(tx)

        log.debug('Waiting for close confirmation event...')
        event = get_event_blocking(
            self.core.channel_manager,
            'ChannelCloseRequested',
            from_block=current_block + 1,
            argument_filters={
                '_sender_address': self.sender,
                '_receiver_address': self.receiver,
                '_open_block_number': self.block
            }
        )

        if event:
            log.debug('Successfully sent channel close request in block {}.'.format(
                event['blockNumber']
            ))
            self.state = Channel.State.settling
            return event
        else:
            log.error('No event received.')
            return None

    def close_cooperatively(self, closing_sig: bytes):
        """
        Attempts to close the channel immediately by providing a hash of the channel's balance
        proof signed by the receiver. This signature must correspond to the balance proof stored in
        the passed channel state.
        """
        if self.state == Channel.State.closed:
            log.error('Channel must not be closed already to be closed cooperatively.')
            return None
        log.info('Attempting to cooperatively close channel to {} created at block #{}.'.format(
            self.receiver, self.block
        ))
        current_block = self.core.web3.eth.blockNumber
        receiver_recovered = verify_closing_sig(
            self.sender,
            self.block,
            self.balance,
            closing_sig,
            self.core.channel_manager.address
        )
        if not is_same_address(receiver_recovered, self.receiver):
            log.error('Invalid closing signature.')
            return None

        tx = create_signed_contract_transaction(
            self.core.private_key,
            self.core.channel_manager,
            'cooperativeClose',
            [
                self.receiver,
                self.block,
                self.balance,
                self.balance_sig,
                closing_sig
            ]
        )
        self.core.web3.eth.sendRawTransaction(tx)

        log.debug('Waiting for settle confirmation event...')
        event = get_event_blocking(
            self.core.channel_manager,
            'ChannelSettled',
            from_block=current_block + 1,
            argument_filters={
                '_sender_address': self.sender,
                '_receiver_address': self.receiver,
                '_open_block_number': self.block
            }
        )

        if event:
            log.debug('Successfully closed channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            return event
        else:
            log.error('No event received.')
            return None

    def settle(self):
        """
        Attempts to settle a channel that has passed its settlement period. If a channel cannot be
        settled yet, the call is ignored with a warning. Blocks until a confirmation event is
        received or timeout.
        """
        if self.state != Channel.State.settling:
            log.error('Channel must be in the settlement period to settle.')
            return None
        log.info('Attempting to settle channel to {} created at block #{}.'.format(
            self.receiver, self.block
        ))

        _, _, settle_block, _, _ = self.core.channel_manager.call().getChannelInfo(
            self.sender, self.receiver, self.block
        )

        current_block = self.core.web3.eth.blockNumber
        wait_remaining = settle_block - current_block
        if wait_remaining > 0:
            log.warning('{} more blocks until this channel can be settled. Aborting.'.format(
                wait_remaining
            ))
            return None

        tx = create_signed_contract_transaction(
            self.core.private_key,
            self.core.channel_manager,
            'settle',
            [
                self.receiver,
                self.block
            ]
        )
        self.core.web3.eth.sendRawTransaction(tx)

        log.debug('Waiting for settle confirmation event...')
        event = get_event_blocking(
            self.core.channel_manager,
            'ChannelSettled',
            from_block=current_block + 1,
            argument_filters={
                '_sender_address': self.sender,
                '_receiver_address': self.receiver,
                '_open_block_number': self.block
            }
        )

        if event:
            log.debug('Successfully settled channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            self.on_settle(self)
            return event
        else:
            log.error('No event received.')
            return None

    def create_transfer(self, value):
        """
        Updates the given channel's balance and balance signature with the new value. The signature
        is returned and stored in the channel state.
        """
        assert value >= 0
        if value > self.deposit - self.balance:
            log.error(
                'Insufficient funds on channel. Needed: {}. Available: {}/{}.'
                .format(value, self.deposit - self.balance, self.deposit)
            )
            return None

        log.debug('Signing new transfer of value {} on channel to {} created at block #{}.'.format(
            value, self.receiver, self.block
        ))

        if self.state == Channel.State.closed:
            log.error('Channel must be open to create a transfer.')
            return None

        self.update_balance(self.balance + value)

        return self.balance_sig

    def is_valid(self) -> bool:
        return self.sign() == self.balance_sig and self.balance <= self.deposit

    def is_suitable(self, value: int):
        return self.deposit - self.balance >= value

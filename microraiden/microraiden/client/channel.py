import logging
from enum import Enum

from eth_utils import decode_hex, is_same_address
from microraiden.crypto import sign_balance_proof, verify_balance_proof

log = logging.getLogger(__name__)


class Channel:
    class State(Enum):
        open = 1
        settling = 2
        closed = 3

    def __init__(
            self,
            client,
            sender: str,
            receiver: str,
            block: int,
            deposit=0,
            balance=0,
            state=State.open
    ):
        self._balance = 0
        self._balance_sig = None

        self.client = client
        self.sender = sender.lower()
        self.receiver = receiver.lower()
        self.deposit = deposit
        self.block = block
        self.balance = balance
        self.state = state

        assert self.block is not None
        assert self._balance_sig

    @staticmethod
    def deserialize(client, channels_raw: dict):
        return [
            Channel(client, craw['sender'], craw['receiver'], craw['block'], craw['balance'])
            for craw in channels_raw
        ]

    @staticmethod
    def serialize(channels):
        return [
            {
                'sender': c.sender,
                'receiver': c.receiver,
                'block': c.block,
                'balance': c.balance

            } for c in channels
        ]

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        self._balance = value
        self._balance_sig = self.sign()
        self.client.store_channels()

    @property
    def balance_sig(self):
        return self._balance_sig

    def sign(self):
        return sign_balance_proof(
            self.client.privkey, self.receiver, self.block, self.balance
        )

    def topup(self, deposit):
        """
        Attempts to increase the deposit in an existing channel. Block until confirmation.
        """
        if self.state != Channel.State.open:
            log.error('Channel must be open to be topped up.')
            return

        token_balance = self.client.token_proxy.contract.call().balanceOf(self.client.account)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified topup ({}/{})'
                .format(token_balance, deposit)
            )

        log.info('Topping up channel to {} created at block #{} by {} tokens.'.format(
            self.receiver, self.block, deposit
        ))
        current_block = self.client.web3.eth.blockNumber

        data = decode_hex(self.receiver) + self.block.to_bytes(4, byteorder='big')
        tx = self.client.token_proxy.create_signed_transaction(
            'transfer', [self.client.channel_manager_address, deposit, data]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for topup confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_topped_up_event_blocking(
            self.sender,
            self.receiver,
            self.block,
            self.deposit + deposit,
            deposit,
            current_block + 1
        )

        if event:
            log.info('Successfully topped up channel in block {}.'.format(event['blockNumber']))
            self.deposit += deposit
            self.client.store_channels()
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
        current_block = self.client.web3.eth.blockNumber

        if balance is not None:
            self.balance = balance

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'close', [self.receiver, self.block, self.balance, self.balance_sig]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for close confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_close_requested_event_blocking(
            self.sender, self.receiver, self.block, current_block + 1
        )

        if event:
            log.info('Successfully sent channel close request in block {}.'.format(
                event['blockNumber']
            ))
            self.state = Channel.State.settling
            self.client.store_channels()
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
        current_block = self.client.web3.eth.blockNumber
        if not is_same_address(
                verify_balance_proof(self.receiver, self.block, self.balance, closing_sig),
                self.receiver
        ):
            log.error('Invalid closing signature.')
            return None

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'close', [self.receiver, self.block, self.balance, self.balance_sig, closing_sig]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for settle confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_settle_event_blocking(
            self.sender, self.receiver, self.block, current_block + 1
        )

        if event:
            log.info('Successfully closed channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            self.client.store_channels()
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

        _, _, settle_block, _ = self.client.channel_manager_proxy.contract.call().getChannelInfo(
            self.sender, self.receiver, self.block
        )

        current_block = self.client.web3.eth.blockNumber
        wait_remaining = settle_block - current_block
        if wait_remaining > 0:
            log.warning('{} more blocks until this channel can be settled. Aborting.'.format(
                wait_remaining
            ))
            return None

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'settle', [self.receiver, self.block]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for settle confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_settle_event_blocking(
            self.sender, self.receiver, self.block, current_block + 1
        )

        if event:
            log.info('Successfully settled channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            self.client.channels.remove(self)
            self.client.store_channels()
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

        log.info('Signing new transfer of value {} on channel to {} created at block #{}.'.format(
            value, self.receiver, self.block
        ))

        if self.state == Channel.State.closed:
            log.error('Channel must be open to create a transfer.')
            return None

        self.balance += value

        self.client.store_channels()

        return self.balance_sig

    def is_valid(self) -> bool:
        return self.sign() == self.balance_sig and self.balance <= self.deposit

    def is_suitable(self, value: int):
        return self.deposit - self.balance >= value

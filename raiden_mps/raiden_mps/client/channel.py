import logging
from enum import Enum

from eth_utils import encode_hex, decode_hex
from raiden_mps.crypto import sign_balance_proof, verify_closing_signature

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
            deposit: int,
            block: int,
            balance=0,
            balance_sig=None,
            state=State.open
    ):
        self.client = client
        self.sender = sender.lower()
        self.receiver = receiver.lower()
        self.deposit = deposit
        self.block = block
        self.balance = balance
        self.balance_sig = balance_sig
        self.state = state

        assert self.block is not None

        if not self.balance_sig:
            self.balance_sig = sign_balance_proof(
                self.client.privkey, self.receiver, self.block, self.balance,
                self.client.channel_manager_address
            )

    @staticmethod
    def deserialize(client, channels_raw):
        for channel_raw in channels_raw:
            channel_raw['client'] = client
            channel_raw['state'] = Channel.State[channel_raw['state']]
            if channel_raw['balance_sig']:
                channel_raw['balance_sig'] = decode_hex(channel_raw['balance_sig'])
        return [Channel(**channel_raw) for channel_raw in channels_raw]

    @staticmethod
    def serialize(channels):
        channels_raw = []
        for channel in channels:
            channel_raw = channel.__dict__.copy()
            channel_raw['state'] = channel.state.name
            if channel.balance_sig:
                channel_raw['balance_sig'] = encode_hex(channel.balance_sig)
            else:
                channel_raw['balance_sig'] = None
            del channel_raw['client']
            channels_raw.append(channel_raw)

        return channels_raw

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
            self.create_transfer(0)

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
        receiver_rec = verify_closing_signature(self.balance_sig, closing_sig)
        if receiver_rec != self.receiver:
            log.error('Invalid closing signature or balance signature.')
            return None

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'close', [
                self.receiver, self.block, self.balance, self.balance_sig, closing_sig
            ]
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

        self.balance_sig = sign_balance_proof(
            self.client.privkey, self.receiver, self.block, self.balance,
            self.client.channel_manager_address
        )

        self.client.store_channels()

        return self.balance_sig

    def is_suitable(self, value: int):
        return self.deposit - self.balance >= value

import logging
from typing import List

from eth_utils import decode_hex, is_same_address
from web3 import Web3
from web3.providers.rpc import RPCProvider

from microraiden.utils import (
    get_private_key,
    get_logs,
    get_event_blocking,
    create_signed_contract_transaction
)

from microraiden.config import CHANNEL_MANAGER_ADDRESS
from microraiden.client.core import Core
from microraiden.client.channel import Channel

log = logging.getLogger(__name__)


class Client:
    def __init__(
            self,
            private_key: str = None,
            key_path: str = None,
            key_password_path: str = None,
            channel_manager_address: str = CHANNEL_MANAGER_ADDRESS,
            web3: Web3 = None
    ) -> None:
        assert private_key or key_path
        assert not private_key or isinstance(private_key, str)

        # Load private key from file if none is specified on command line.
        if not private_key:
            private_key = get_private_key(key_path, key_password_path)
            assert private_key is not None

        self.channels = []  # type: List[Channel]

        # Create web3 context if none is provided, either by using the proxies' context or creating
        # a new one.
        if not web3:
            web3 = Web3(RPCProvider())

        self.core = Core(private_key, web3, channel_manager_address)

        self.sync_channels()

    def __enter__(self):
        return self

    def sync_channels(self):
        """
        Merges locally available channel information, including their current balance signatures,
        with channel information available on the blockchain to make up for local data loss.
        Naturally, balance signatures cannot be recovered from the blockchain.
        """
        filters = {'_sender': self.core.address}
        create = get_logs(
            self.core.channel_manager,
            'ChannelCreated',
            argument_filters=filters
        )
        topup = get_logs(
            self.core.channel_manager,
            'ChannelToppedUp',
            argument_filters=filters
        )
        close = get_logs(
            self.core.channel_manager,
            'ChannelCloseRequested',
            argument_filters=filters
        )
        settle = get_logs(
            self.core.channel_manager,
            'ChannelSettled',
            argument_filters=filters
        )

        channel_key_to_channel = {}

        def get_channel(event) -> Channel:
            sender = event['args']['_sender']
            receiver = event['args']['_receiver']
            block = event['args'].get('_open_block_number', event['blockNumber'])
            assert sender == self.core.address
            return channel_key_to_channel.get((sender, receiver, block), None)

        for c in self.channels:
            channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in create:
            c = get_channel(e)
            if c:
                c.deposit = e['args']['_deposit']
            else:
                c = Channel(
                    self.core,
                    e['args']['_sender'],
                    e['args']['_receiver'],
                    e['blockNumber'],
                    e['args']['_deposit'],
                    on_settle=lambda channel: self.channels.remove(channel)
                )
                assert c.sender == self.core.address
                channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in topup:
            c = get_channel(e)
            c.deposit += e['args']['_added_deposit']

        for e in close:
            # Requested closed, not actual closed.
            c = get_channel(e)

            c.update_balance(e['args']['_balance'])
            c.state = Channel.State.settling

        for e in settle:
            c = get_channel(e)
            c.state = Channel.State.closed

        # Forget closed channels.
        self.channels = [
            c for c in channel_key_to_channel.values() if c.state != Channel.State.closed
        ]

        log.debug('Synced a total of {} channels.'.format(len(self.channels)))

    def open_channel(self, receiver_address: str, deposit: int):
        """
        Attempts to open a new channel to the receiver with the given deposit. Blocks until the
        creation transaction is found in a pending block or timeout is reached. The new channel
        state is returned.
        """
        assert isinstance(receiver_address, str)
        assert isinstance(deposit, int)
        assert deposit > 0

        token_balance = self.core.token.call().balanceOf(self.core.address)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified deposit ({}/{})'
                .format(token_balance, deposit)
            )
            return None

        current_block = self.core.web3.eth.blockNumber
        log.info('Creating channel to {} with an initial deposit of {} @{}'.format(
            receiver_address, deposit, current_block
        ))

        data = decode_hex(receiver_address)
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

        log.debug('Waiting for channel creation event on the blockchain...')
        filters = {
            '_sender': self.core.address,
            '_receiver': receiver_address
        }
        event = get_event_blocking(
            self.core.channel_manager,
            'ChannelCreated',
            from_block=current_block + 1,
            argument_filters=filters
        )

        if event:
            log.debug('Event received. Channel created in block {}.'.format(event['blockNumber']))
            channel = Channel(
                self.core,
                event['args']['_sender'],
                event['args']['_receiver'],
                event['blockNumber'],
                event['args']['_deposit'],
                on_settle=lambda c: self.channels.remove(c)
            )
            self.channels.append(channel)
        else:
            log.error('Error: No event received.')
            channel = None

        return channel

    def get_open_channels(self, receiver: str = None) -> List[Channel]:
        """
        Returns all open channels to the given receiver. If no receiver is specified, all open
        channels are returned.
        """
        return [
            c for c in self.channels
            if is_same_address(c.sender, self.core.address) and
            (not receiver or is_same_address(c.receiver, receiver)) and
            c.state == Channel.State.open
        ]

    def get_suitable_channel(
            self, receiver, value, initial_deposit=lambda x: x, topup_deposit=lambda x: x
    ) -> Channel:
        """
        Searches stored channels for one that can sustain the given transfer value. If none is
        found, a possibly open channel is topped up using the topup callable to determine its topup
        value. If both attempts fail, a new channel is created based on the initial deposit
        callable.
        Note: In the realistic case that only one channel is opened per (sender,receiver) pair,
        this method usually performs like this:
        1. Directly return open channel if sufficiently funded.
        2. Topup existing open channel if insufficiently funded.
        3. Create new channel if no open channel exists.
        If topping up or creating fails, this method returns None.
        Channels are topped up just enough so that their remaining capacity equals
        topup_deposit(value).
        """
        open_channels = self.get_open_channels(receiver)
        suitable_channels = [c for c in open_channels if c.is_suitable(value)]

        if suitable_channels:
            # At least one channel with sufficient funds.

            if len(suitable_channels) > 1:
                # This is not impossible but should only happen after bad channel management.
                log.warning(
                    'Warning: {} suitable channels found. '
                    'Choosing the one with the lowest remaining capacity.'
                    .format(len(suitable_channels))
                )

            capacity, channel = min(
                ((c.deposit - c.balance, c) for c in suitable_channels), key=lambda x: x[0]
            )
            log.debug(
                'Found suitable open channel, opened at block #{}.'.format(channel.block)
            )
            return channel

        elif open_channels:
            # Open channel(s) but insufficient funds. Requires topup.

            if len(open_channels) > 1:
                # This is not impossible but should only happen after bad channel management.
                log.warning(
                    'Warning: {} open channels for topup found. '
                    'Choosing the one with the highest remaining capacity.'
                    .format(len(open_channels))
                )

            capacity, channel = max(
                ((c.deposit - c.balance, c) for c in open_channels), key=lambda x: x[0]
            )
            deposit = max(value, topup_deposit(value)) - capacity
            event = channel.topup(deposit)
            return channel if event else None

        else:
            # No open channels to receiver. Create a new one.
            deposit = max(value, initial_deposit(value))
            return self.open_channel(receiver, deposit)

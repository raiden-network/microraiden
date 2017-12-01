import json
import logging
import os
from typing import List

import click
import filelock
from eth_utils import decode_hex, is_same_address
from web3 import Web3
from web3.providers.rpc import RPCProvider

from microraiden.utils import get_private_key
from microraiden.config import (
    CHANNEL_MANAGER_ADDRESS,
    GAS_LIMIT,
    GAS_PRICE,
    NETWORK_NAMES,
    CONTRACT_METADATA
)
from microraiden.contract_proxy import ContractProxy, ChannelContractProxy
from microraiden.crypto import privkey_to_addr
from .channel import Channel
from microraiden.config import TOKEN_ABI_NAME

CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'

log = logging.getLogger(__name__)


class Client:
    def __init__(
            self,
            privkey: str = None,
            key_path: str = None,
            key_password_path: str = None,
            datadir: str = click.get_app_dir('microraiden'),
            channel_manager_address: str = CHANNEL_MANAGER_ADDRESS,
            web3: Web3 = None,
            channel_manager_proxy: ChannelContractProxy = None,
            token_proxy: ContractProxy = None,
            contract_metadata: dict = CONTRACT_METADATA
    ) -> None:
        assert privkey or key_path
        assert not privkey or isinstance(privkey, str)

        # Plain copy initializations.
        self.privkey = privkey
        self.datadir = datadir
        self.channel_manager_address = channel_manager_address
        self.web3 = web3
        self.channel_manager_proxy = channel_manager_proxy
        self.token_proxy = token_proxy

        # Load private key from file if none is specified on command line.
        if not privkey:
            self.privkey = get_private_key(key_path, key_password_path)
            assert self.privkey is not None

        os.makedirs(datadir, exist_ok=True)
        assert os.path.isdir(datadir)

        self.account = privkey_to_addr(self.privkey)
        self.channels = []  # type: List[Channel]

        # Create web3 context if none is provided, either by using the proxies' context or creating
        # a new one.
        if not web3:
            if channel_manager_proxy:
                self.web3 = channel_manager_proxy.web3
                self.channel_manager_address = channel_manager_proxy.address
            elif token_proxy:
                self.web3 = token_proxy.web3
            else:
                self.web3 = Web3(RPCProvider())

        # Create missing contract proxies.
        if not channel_manager_proxy:
            channel_manager_abi = contract_metadata[CHANNEL_MANAGER_ABI_NAME]['abi']
            self.channel_manager_proxy = ChannelContractProxy(
                self.web3,
                self.privkey,
                channel_manager_address,
                channel_manager_abi,
                GAS_PRICE,
                GAS_LIMIT
            )

        token_address = self.channel_manager_proxy.contract.call().token()
        if not token_proxy:
            token_abi = contract_metadata[TOKEN_ABI_NAME]['abi']
            self.token_proxy = ContractProxy(
                self.web3, self.privkey, token_address, token_abi, GAS_PRICE, GAS_LIMIT
            )
        else:
            assert is_same_address(self.token_proxy.address, token_address)

        assert self.web3
        assert self.channel_manager_proxy
        assert self.token_proxy
        assert self.channel_manager_proxy.web3 == self.web3 == self.token_proxy.web3

        netid = self.web3.version.network
        self.balances_filename = 'balances_{}_{}.json'.format(
            NETWORK_NAMES.get(netid, netid), self.account[:10]
        )

        self.filelock = filelock.FileLock(os.path.join(self.datadir, self.balances_filename))
        self.filelock.acquire(timeout=0)

        self.load_channels()
        self.sync_channels()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.filelock.release()

    def sync_channels(self):
        """
        Merges locally available channel information, including their current balance signatures,
        with channel information available on the blockchain to make up for local data loss.
        Naturally, balance signatures cannot be recovered from the blockchain.
        """
        filters = {'_sender': self.account}
        create = self.channel_manager_proxy.get_channel_created_logs(filters=filters)
        close = self.channel_manager_proxy.get_channel_close_requested_logs(filters=filters)
        settle = self.channel_manager_proxy.get_channel_settled_logs(filters=filters)
        topup = self.channel_manager_proxy.get_channel_topped_up_logs(filters=filters)

        channel_key_to_channel = {}

        def get_channel(event):
            sender = event['args']['_sender']
            receiver = event['args']['_receiver']
            block = event['args'].get('_open_block_number', event['blockNumber'])
            assert sender == self.account
            return channel_key_to_channel.get((sender, receiver, block), None)

        for c in self.channels:
            channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in create:
            c = get_channel(e)
            if c:
                c.deposit = e['args']['_deposit']
            else:
                c = Channel(
                    self,
                    e['args']['_sender'],
                    e['args']['_receiver'],
                    e['blockNumber'],
                    e['args']['_deposit']
                )
                assert c.sender == self.account
                channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in topup:
            c = get_channel(e)
            c.deposit += e['args']['_added_deposit']

        for e in close:
            # Requested closed, not actual closed.
            c = get_channel(e)

            c.balance = e['args']['_balance']
            c.state = Channel.State.settling

        for e in settle:
            c = get_channel(e)
            c.state = Channel.State.closed

        # Forget closed channels.
        self.channels = [
            c for c in channel_key_to_channel.values() if c.state != Channel.State.closed
        ]
        self.store_channels()

        log.info('Synced a total of {} channels.'.format(len(self.channels)))

    def load_channels(self):
        """
        Loads the locally available channel storage if it exists.
        """
        channels_path = os.path.join(self.datadir, self.balances_filename)
        if not os.path.exists(channels_path) or os.path.getsize(channels_path) == 0:
            return
        with open(channels_path) as channels_file:
            try:
                store = json.load(channels_file)
                if isinstance(store, dict) and self.channel_manager_address in store:
                    self.channels = Channel.deserialize(self, store[self.channel_manager_address])
            except ValueError:
                log.warning('Failed to load local channel storage.')

        log.info('Loaded {} channels from disk.'.format(len(self.channels)))

    def store_channels(self):
        """
        Writes the current channel storage to the local storage.
        """
        os.makedirs(self.datadir, exist_ok=True)

        store_path = os.path.join(self.datadir, self.balances_filename)
        if os.path.exists(store_path):
            with open(store_path) as channels_file:
                try:
                    store = json.load(channels_file)
                except ValueError:
                    store = dict()
        else:
            store = dict()
        if not isinstance(store, dict):
            store = dict()

        with open(store_path, 'w') as channels_file:
            store[self.channel_manager_address] = Channel.serialize(self.channels)
            json.dump(store, channels_file, indent=4)

    def open_channel(self, receiver_address: str, deposit: int):
        """
        Attempts to open a new channel to the receiver with the given deposit. Blocks until the
        creation transaction is found in a pending block or timeout is reached. The new channel
        state is returned.
        """
        assert isinstance(receiver_address, str)
        assert isinstance(deposit, int)
        assert deposit > 0

        token_balance = self.token_proxy.contract.call().balanceOf(self.account)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified deposit ({}/{})'
                .format(token_balance, deposit)
            )

        current_block = self.web3.eth.blockNumber
        log.info('Creating channel to {} with an initial deposit of {} @{}'.format(
            receiver_address, deposit, current_block
        ))

        data = decode_hex(receiver_address)
        tx = self.token_proxy.create_signed_transaction(
            'transfer', [self.channel_manager_address, deposit, data]
        )
        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(
            self.account, receiver_address, current_block + 1
        )

        if event:
            log.info('Event received. Channel created in block {}.'.format(event['blockNumber']))
            channel = Channel(
                self,
                event['args']['_sender'],
                event['args']['_receiver'],
                event['blockNumber'],
                event['args']['_deposit']
            )
            self.channels.append(channel)
            self.store_channels()
        else:
            log.info('Error: No event received.')
            channel = None

        return channel

    def get_open_channels(self, receiver: str = None) -> List[Channel]:
        """
        Returns all open channels to the given receiver. If no receiver is specified, all open
        channels are returned.
        """
        return [
            c for c in self.channels
            if is_same_address(c.sender, self.account.lower()) and
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
            log.info(
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

import json
import os
import logging

from ethereum.utils import privtoaddr, encode_hex, decode_hex
from web3 import Web3
from web3.providers.rpc import RPCProvider

from raiden_mps.client.channel_info import ChannelInfo
from raiden_mps.contract_proxy import ContractProxy, ChannelContractProxy
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS, TOKEN_ADDRESS

CHANNELS_DB = 'channels.json'
GAS_PRICE = 20 * 1000 * 1000 * 1000
GAS_LIMIT = 314159
CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'
TOKEN_ABI_NAME = 'Token'

log = logging.getLogger(__name__)

if isinstance(encode_hex(b''), bytes):
    _encode_hex = encode_hex
    encode_hex = lambda b: _encode_hex(b).decode()


class RMPClient:
    def __init__(
            self,
            private_key,
            channel_manager_proxy,
            token_proxy,
            datadir=os.path.join(os.path.expanduser('~'), '.raiden'),
            channel_manager_address=CHANNEL_MANAGER_ADDRESS,
            token_address=TOKEN_ADDRESS
    ):
        assert isinstance(private_key, str)
        assert isinstance(channel_manager_proxy, ChannelContractProxy)
        assert isinstance(token_proxy, ContractProxy)
        assert os.path.isdir(datadir)

        self.datadir = datadir
        self.channel_manager_address = channel_manager_address
        self.token_address = token_address
        self.channels = []

        self.privkey = private_key
        self.account = '0x' + encode_hex(privtoaddr(self.privkey))

        self.web3 = channel_manager_proxy.web3
        self.channel_manager_proxy = channel_manager_proxy
        self.token_proxy = token_proxy

        self.load_channels()
        self.sync_channels()

    def sync_channels(self):
        """
        Merges locally available channel information, including their current balance signatures, with channel
        information available on the blockchain to make up for local data loss. Naturally, balance signatures cannot be
        recovered from the blockchain. Closed channels are discarded from local storage.
        """
        filters = {'_sender': self.account}
        created_events = self.channel_manager_proxy.get_channel_created_logs(filters=filters)
        close_requested_events = self.channel_manager_proxy.get_channel_close_requested_logs(filters=filters)
        settled_events = self.channel_manager_proxy.get_channel_settled_logs(filters=filters)
        topup_events = self.channel_manager_proxy.get_channel_topped_up_logs(filters=filters)

        created_channels = [ChannelInfo.from_event(event, ChannelInfo.State.open) for event in created_events]
        settling_channels = [
            ChannelInfo.from_event(event, ChannelInfo.State.settling) for event in close_requested_events
        ]
        closed_channels = [ChannelInfo.from_event(event, ChannelInfo.State.closed) for event in settled_events]
        toppedup_channels = [ChannelInfo.from_event(event, ChannelInfo.State.open) for event in topup_events]

        self.channels = ChannelInfo.merge_infos(
            self.channels, created_channels, settling_channels, closed_channels, toppedup_channels
        )
        self.store_channels()

        log.info('Synced a total of {} channels.'.format(len(self.channels)))

    def load_channels(self):
        """
        Loads the locally available channel storage if it exists.
        """
        channels_path = os.path.join(self.datadir, CHANNELS_DB)
        if not os.path.exists(channels_path):
            return
        with open(channels_path) as channels_file:
            try:
                store = json.load(channels_file)
                if isinstance(store, dict) and self.channel_manager_address in store:
                    self.channels = ChannelInfo.deserialize(store[self.channel_manager_address])
            except json.decoder.JSONDecodeError:
                log.warning('Failed to load local channel storage.')

        log.info('Loaded {} channels from disk.'.format(len(self.channels)))

    def store_channels(self):
        """
        Writes the current channel storage to the local storage.
        """
        os.makedirs(self.datadir, exist_ok=True)

        store_path = os.path.join(self.datadir, CHANNELS_DB)
        if os.path.exists(store_path):
            with open(store_path) as channels_file:
                try:
                    store = json.load(channels_file)
                except json.decoder.JSONDecodeError:
                    store = dict()
        else:
            store = dict()
        if not isinstance(store, dict):
            store = dict()

        with open(store_path, 'w') as channels_file:
            store[self.channel_manager_address] = ChannelInfo.serialize(self.channels)
            json.dump(store, channels_file, indent=4)

    def open_channel(self, receiver_address, deposit):
        """
        Attempts to open a new channel to the receiver with the given deposit. Blocks until the creation transaction is
        found in a pending block or timeout is reached. The new channel state is returned.
        """
        assert isinstance(receiver_address, str)
        assert isinstance(deposit, int)
        assert deposit > 0
        receiver_bytes = decode_hex(receiver_address.replace('0x', ''))
        log.info('Creating channel to {} with an initial deposit of {}.'.format(receiver_address, deposit))
        current_block = self.web3.eth.blockNumber
        tx1 = self.token_proxy.create_transaction('approve', [self.channel_manager_address, deposit])
        tx2 = self.channel_manager_proxy.create_transaction('createChannel', [receiver_bytes, deposit], nonce_offset=1)
        self.web3.eth.sendRawTransaction(tx1)
        self.web3.eth.sendRawTransaction(tx2)

        log.info('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(self.account, receiver_address, current_block + 1)

        if event:
            log.info('Event received. Channel created in block {}.'.format(event['blockNumber']))
            channel = ChannelInfo(
                event['args']['_sender'],
                event['args']['_receiver'],
                event['args']['_deposit'],
                event['blockNumber']
            )
            self.channels.append(channel)
            self.store_channels()
        else:
            log.info('Error: No event received.')
            channel = None

        return channel

    def topup_channel(self, channel, value):
        """
        Attempts to increase the deposit in an existing channel. Block until confirmation.
        """
        if channel.state != ChannelInfo.State.open:
            log.error('Channel must be open to be topped up.')
            return

        log.info('Topping up channel to {} created at block #{} by {} tokens.'.format(
            channel.receiver, channel.block, value
        ))
        current_block = self.web3.eth.blockNumber

        tx1 = self.token_proxy.create_transaction('approve', [self.channel_manager_address, value])
        tx2 = self.channel_manager_proxy.create_transaction(
            'topUp', [channel.receiver, channel.block, value], nonce_offset=1
        )
        self.web3.eth.sendRawTransaction(tx1)
        self.web3.eth.sendRawTransaction(tx2)

        log.info('Waiting for topup confirmation event...')
        event = self.channel_manager_proxy.get_channel_topped_up_event_blocking(
            channel.sender, channel.receiver, channel.block, channel.deposit + value, value, current_block + 1
        )

        if event:
            log.info('Successfully topped up channel in block {}.'.format(event['blockNumber']))
            channel.deposit += value
            self.store_channels()
            return event
        else:
            log.error('No event received.')
            return None

    def close_channel(self, channel, balance=None):
        """
        Attempts to request close on a channel. An explicit balance can be given to override the locally stored balance
        signature. Blocks until a confirmation event is received or timeout.
        """
        if channel.state != ChannelInfo.State.open:
            log.error('Channel must be open to request a close.')
            return
        log.info('Requesting close of channel to {} created at block #{}.'.format(channel.receiver, channel.block))
        current_block = self.web3.eth.blockNumber

        if balance:
            channel.balance = 0
            self.create_transfer(channel, balance)
        elif not channel.balance_sig:
            self.create_transfer(channel, 0)

        tx = self.channel_manager_proxy.create_transaction(
            'close', [channel.receiver, channel.block, channel.balance, channel.balance_sig]
        )
        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for close confirmation event...')
        event = self.channel_manager_proxy.get_channel_close_requested_event_blocking(
            channel.sender, channel.receiver, channel.block, current_block + 1
        )

        if event:
            log.info('Successfully sent channel close request in block {}.'.format(event['blockNumber']))
            channel.state = ChannelInfo.State.settling
            self.store_channels()
            return event
        else:
            log.error('No event received.')
            return None

    def close_channel_cooperatively(self, channel, closing_sig):
        """
        Attempts to close the channel immediately by providing a hash of the channel's balance proof signed by the
        receiver. This signature must correspond to the balance proof stored in the passed channel state.
        """
        if channel.state != ChannelInfo.State.open:
            log.error('Channel must be open to be closed cooperatively.')
            return
        log.info('Attempting to cooperatively close channel to {} created at block #{}.'.format(
            channel.receiver, channel.block
        ))
        current_block = self.web3.eth.blockNumber
        receiver_recovered = self.channel_manager_proxy.contract.call().verifyClosingSignature(
            channel.balance_sig, closing_sig
        )
        if receiver_recovered != channel.receiver:
            log.error('Invalid closing signature or balance signature.')
            return

        tx = self.channel_manager_proxy.create_transaction(
            'close', [channel.receiver, channel.block, channel.balance, channel.balance_sig, closing_sig]
        )
        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for settle confirmation event...')
        event = self.channel_manager_proxy.get_channel_settle_event_blocking(
            channel.sender, channel.receiver, channel.block, current_block + 1
        )

        if event:
            log.info('Successfully closed channel in block {}.'.format(event['blockNumber']))
            channel.state = ChannelInfo.State.closed
            self.store_channels()
        else:
            log.error('No event received.')

    def settle_channel(self, channel):
        """
        Attempts to settle a channel that has passed its settlement period. If a channel cannot be settled yet, the call
        is ignored with a warning. Blocks until a confirmation event is received or timeout.
        """
        if channel.state != ChannelInfo.State.settling:
            log.error('Channel must be in the settlement period to settle.')
            return
        log.info('Attempting to settle channel to {} created at block #{}.'.format(channel.receiver, channel.block))

        settle_block = self.channel_manager_proxy.contract.call().getChannelInfo(
            channel.sender, channel.receiver, channel.block
        )[2]

        current_block = self.web3.eth.blockNumber
        wait_remaining = settle_block - current_block
        if wait_remaining > 0:
            log.warning('{} more blocks until this channel can be settled. Aborting.'.format(wait_remaining))
            return

        tx = self.channel_manager_proxy.create_transaction(
            'settle', [channel.receiver, channel.block]
        )
        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for settle confirmation event...')
        event = self.channel_manager_proxy.get_channel_settle_event_blocking(
            channel.sender, channel.receiver, channel.block, current_block + 1
        )

        if event:
            log.info('Successfully settled channel in block {}.'.format(event['blockNumber']))
            channel.state = ChannelInfo.State.closed
            self.store_channels()
        else:
            log.error('No event received.')

    def create_transfer(self, channel, value):
        """
        Updates the given channel's balance and balance signature with the new value. The signature is returned and
        stored in the channel state.
        """
        assert isinstance(channel, ChannelInfo)
        assert value >= 0
        channel.balance += value

        channel.balance_sig = self.channel_manager_proxy.sign_balance_proof(
            self.privkey, channel.receiver, channel.block, channel.balance
        )

        self.store_channels()

        return channel.balance_sig


def rmpc_factory(privkey,
                 rpc_endpoint,
                 rpc_port,
                 datadir,
                 contract_abi_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/contracts.json'),
                 channel_manager_address=CHANNEL_MANAGER_ADDRESS,
                 token_address=TOKEN_ADDRESS):
    rpc = RPCProvider(rpc_endpoint, rpc_port)
    web3 = Web3(rpc)
    with open(contract_abi_path) as abi_file:
        contract_abis = json.load(abi_file)
        channel_manager_abi = contract_abis[CHANNEL_MANAGER_ABI_NAME]['abi']
        token_abi = contract_abis[TOKEN_ABI_NAME]['abi']

    channel_manager_proxy = ChannelContractProxy(
        web3,
        privkey,
        channel_manager_address,
        channel_manager_abi,
        GAS_PRICE,
        GAS_LIMIT
    )

    token_proxy = ContractProxy(
        web3,
        privkey,
        token_address,
        token_abi,
        GAS_PRICE,
        GAS_LIMIT
    )

    return RMPClient(privkey,
                     channel_manager_proxy,
                     token_proxy)

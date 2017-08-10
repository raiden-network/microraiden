from web3 import Web3
from web3.providers.rpc import RPCProvider
from ethereum.utils import privtoaddr, encode_hex
import json
import os
import requests
from enum import Enum

from raiden_mps.contract_proxy import ContractProxy, ChannelContractProxy
from raiden_mps.header import HTTPHeaders

STATUS_OK = 200
STATUS_PAYMENT_REQUIRED = 402
CHANNELS_DB = 'channels.json'
GAS_PRICE = 20 * 1000 * 1000 * 1000
GAS_LIMIT = 314159
CHANNEL_SIZE_FACTOR = 3
CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'
TOKEN_ABI_NAME = 'Token'
HEADERS = HTTPHeaders.as_dict()


class ChannelInfo:
    class State(Enum):
        open = 1
        closed = 2
        settled = 3

    def __init__(self, sender, receiver, deposit, block, balance=0, balance_sig=None, state=State.open):
        self.sender = sender
        self.receiver = receiver
        self.deposit = deposit
        self.block = block
        self.balance = balance
        self.balance_sig = balance_sig
        self.state = state


class M2MClient(object):
    def __init__(
            self,
            api_endpoint,
            api_port,
            datadir,
            rpc_endpoint,
            rpc_port,
            key_path,
            dry_run,
            channel_manager_address,
            contract_abi_path,
            token_address
    ):
        self.api_endpoint = api_endpoint
        self.api_port = api_port
        self.datadir = datadir
        self.rpc_endpoint = rpc_endpoint
        self.rpc_port = rpc_port
        self.channel_manager_address = channel_manager_address
        self.dry_run = dry_run
        if not contract_abi_path:
            contract_abi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/contracts.json')
        with open(contract_abi_path) as abi_file:
            contract_abis = json.load(abi_file)
            self.channel_manager_abi = contract_abis[CHANNEL_MANAGER_ABI_NAME]['abi']
            self.token_abi = contract_abis[TOKEN_ABI_NAME]['abi']
        self.token_address = token_address
        self.channels = []

        with open(key_path) as keyfile:
            self.privkey = keyfile.readline()[:-1]
        self.account = '0x' + encode_hex(privtoaddr(self.privkey))
        self.rpc = RPCProvider(self.rpc_endpoint, self.rpc_port)
        self.web3 = Web3(self.rpc)

        self.channel_manager_proxy = ChannelContractProxy(
            self.web3,
            self.privkey,
            self.channel_manager_address,
            self.channel_manager_abi,
            GAS_PRICE,
            GAS_LIMIT
        )

        self.token_proxy = ContractProxy(
            self.web3,
            self.privkey,
            self.token_address,
            self.token_abi,
            GAS_PRICE,
            GAS_LIMIT
        )

        self.load_channels()

    def load_channels(self):
        channels_path = os.path.join(self.datadir, CHANNELS_DB)
        if not os.path.exists(channels_path):
            return []
        with open(channels_path) as channels_file:
            channels_raw = json.load(channels_file)
            for channel_raw in channels_raw:
                channel_raw['state'] = ChannelInfo.State[channel_raw['state']]
            self.channels = [ChannelInfo(**channel_raw) for channel_raw in channels_raw]

        print('Loaded {} open channels.'.format(len(self.channels)))

    def store_channels(self):
        os.makedirs(self.datadir, exist_ok=True)

        def serialize(o):
            if isinstance(o, bytes):
                return encode_hex(o)
            elif isinstance(o, ChannelInfo.State):
                return o.name
            else:
                return o.__dict__

        with open(os.path.join(self.datadir, CHANNELS_DB), 'w') as channels_file:
            json.dump(self.channels, channels_file, default=serialize, sort_keys=True, indent=4)

    def request_resource(self, resource):
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            channel_manager_address = headers[HEADERS['contract_address']]
            if channel_manager_address != self.channel_manager_address:
                print('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                return None

            price = int(headers[HEADERS['price']])
            print('Preparing payment of price {}.'.format(price))
            channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
            if channel:
                status, headers, body = self.perform_request(resource, channel)

                if status == STATUS_OK:
                    # TODO: use actual cost
                    # print('Resource payment successful. Final cost: {}'.format(headers[HEADERS['cost']]))
                    print('Resource payment successful. Final cost: {}'.format(0))
                elif status == STATUS_PAYMENT_REQUIRED:
                    if HEADERS['insuf_funds'] in headers:
                        print('Error: Insufficient funds in channel for balance proof.')
                    elif HEADERS['insuf_confs'] in headers:
                        print('Error: Newly created channel does not have enough confirmations yet.')
                    else:
                        print('Error: Unknown error.')
            else:
                print('Error: Could not perform the payment.')

        else:
            print('Error code {} while requesting resource: {}'.format(status, body))

    def perform_payment(self, receiver, value):
        channels = [
            channel for channel in self.channels
            if channel.sender.lower() == self.account.lower() and channel.receiver.lower() == receiver.lower() and
               channel.state == ChannelInfo.State.open
        ]
        assert len(channels) < 2

        if channels:
            channel = channels[0]
            print('Found open channel, opened at block #{}.'.format(channel.block))
        else:
            deposit = CHANNEL_SIZE_FACTOR * value
            print('Creating new channel with deposit {} for receiver {}.'.format(deposit, receiver))
            channel = self.open_channel(receiver, deposit)

        if channel:
            self.create_transfer(channel, value)
            return channel
        else:
            return None

    def perform_request(self, resource, channel=None):
        if channel:
            headers = {
                HEADERS['contract_address']: self.channel_manager_address,
                HEADERS['balance']: str(channel.balance),
                HEADERS['balance_signature']: encode_hex(channel.balance_sig),
                HEADERS['sender_address']: channel.sender,
                HEADERS['receiver_address']: channel.receiver,
                HEADERS['open_block']: str(channel.block)
            }
        else:
            headers = None
        url = 'http://{}:{}/{}'.format(self.api_endpoint, self.api_port, resource)
        response = requests.get(url, headers=headers)
        return response.status_code, response.headers, response.content

    def open_channel(self, receiver, deposit):
        current_block = self.web3.eth.blockNumber
        tx1 = self.token_proxy.create_transaction('approve', [self.channel_manager_address, deposit])
        tx2 = self.channel_manager_proxy.create_transaction('createChannel', [receiver, deposit], nonce_offset=1)
        if not self.dry_run:
            self.web3.eth.sendRawTransaction(tx1)
            self.web3.eth.sendRawTransaction(tx2)

        print('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(self.account, receiver, current_block + 1)

        if event:
            print('Event received. Channel created in block {}.'.format(event['blockNumber']))
            channel = ChannelInfo(
                event['args']['_sender'],
                event['args']['_receiver'],
                event['args']['_deposit'],
                event['blockNumber']
            )
            self.channels.append(channel)
            self.store_channels()
        else:
            print('Error: No event received.')
            channel = None

        return channel

    def topup_channel(self):
        pass

    def settle_channel(self):
        pass

    def close_channel(self, channel):
        assert channel in self.channels
        print('Closing channel to {}.'.format(channel.receiver))
        current_block = self.web3.eth.blockNumber

        tx = self.channel_manager_proxy.create_transaction(
            'close', [channel.receiver, channel.block, channel.balance, channel.balance_sig]
        )
        if not self.dry_run:
            self.web3.eth.sendRawTransaction(tx)

        print('Waiting for close confirmation event.')
        event = self.channel_manager_proxy.get_channel_requested_close_event_blocking(
            channel.sender, channel.receiver, current_block + 1
        )

        if event:
            print('Successfully sent channel close request in block {}.'.format(event['blockNumber']))
        else:
            print('Error: No event received.')

    def create_transfer(self, channel, value):
        assert channel in self.channels

        channel.balance += value

        channel.balance_sig = self.channel_manager_proxy.sign_balance_proof(
            self.privkey, channel.receiver, channel.block, channel.balance
        )

        # This part is optional but can't hurt.
        sender = self.channel_manager_proxy.contract.call().verifyBalanceProof(
            channel.receiver, channel.block, channel.balance, channel.balance_sig
        )
        assert sender == channel.sender

        self.store_channels()

        return channel.balance_sig

from collections import namedtuple

from web3 import Web3
from web3.providers.rpc import RPCProvider
from ethereum.utils import privtoaddr, encode_hex, ecsign
import json
import os
import requests

from raiden_mps.contract_proxy import ContractProxy, ChannelContractProxy
from raiden_mps.header import HTTPHeaders

STATUS_OK = 200
STATUS_PAYMENT_REQUIRED = 402
CHANNELS_DB = 'channels.json'
GAS_PRICE = 20 * 1000 * 1000 * 1000
GAS_LIMIT = 314159
CHANNEL_SIZE_FACTOR = 10
CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'
TOKEN_ABI_NAME = 'Token'
HEADERS = HTTPHeaders.as_dict()

ChannelInfo = namedtuple('ChannelInfo', ['sender', 'receiver', 'deposit', 'balance', 'block', 'balance_proof'])
BalanceProof = namedtuple('BalanceProof', ['balance', 'balance_signature'])


class M2MClient(object):
    def perform_payment(self, receiver, value):
        channels = [
            channel for channel in self.channels
            if channel.sender == self.account and channel.receiver == receiver
        ]
        assert len(channels) < 2

        if channels:
            channel = channels[0]
        else:
            deposit = CHANNEL_SIZE_FACTOR * value
            print('Creating new channel with deposit {} for receiver {}.'.format(receiver, deposit))
            channel = self.open_channel(receiver, deposit)

        return self.create_transfer(channel, value)

    def perform_request(self, resource, balance_proof=None):
        if balance_proof:
            headers = {
                HEADERS['balance']: balance_proof[0],
                HEADERS['balance_signature']: balance_proof[1]
            }
        else:
            headers = None
        url = 'http://{}:{}/{}'.format(self.api_endpoint, self.api_port, resource)
        response = requests.get(url, headers=headers)
        return response.status_code, response.headers, response.json()

    def request_resource(self, resource):
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            channel_manager_address = headers[HEADERS['contract_address']]
            if channel_manager_address != self.channel_manager_address:
                print('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                return None

            price = int(headers[HEADERS['price']])
            print('Preparing payment of price {}.'.format(price))
            balance_proof = self.perform_payment(headers[HEADERS['receiver_address']], price)
            status, headers, body = self.perform_request(resource, balance_proof)

            if status == STATUS_OK:
                print('Resource payment successful. Final cost: {}'.format(headers[HEADERS['cost']]))
            elif status == STATUS_PAYMENT_REQUIRED:
                if HEADERS['insuf_funds'] in headers:
                    print('Error: Insufficient funds in channel for balance proof.')
                    return None
                elif HEADERS['insuf_confs'] in headers:
                    print('Error: Newly created channel does not have enough confirmations yet.')
                    return None
                else:
                    print('Error: Unknown error.')
                    return None

        else:
            print('Error code {} while requesting resource: {}', status, body)

    def load_channels(self):
        channels_path = os.path.join(self.datadir, CHANNELS_DB)
        if not os.path.exists(channels_path):
            return []
        with open(channels_path) as channels_file:
            channels_raw = json.load(channels_file)
            self.channels = [namedtuple('ChannelInfo', channel.keys())(**channel) for channel in channels_raw]
        print('Loaded {} open channels.'.format(len(self.channels)))

    def store_channels(self):
        os.makedirs(self.datadir, exist_ok=True)
        with open(os.path.join(self.datadir, CHANNELS_DB), 'w') as channels_file:
            self.channels = json.dump([channel._asdict() for channel in self.channels], channels_file)

    def open_channel(self, receiver, deposit):
        current_block = self.web3.eth.blockNumber
        tx1 = self.token_proxy.create_transaction('approve', [self.channel_manager_address, deposit])
        tx2 = self.channel_manager_proxy.create_transaction('createChannel', [receiver, deposit], nonce_offset=1)
        if not self.dry_run:
            self.web3.eth.sendRawTransaction(tx1)
            self.web3.eth.sendRawTransaction(tx2)

        print('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(self.account, receiver, current_block + 1)
        print('Event received. Channel created in block {}.'.format(event['blockNumber']))
        # self.web3._requestManager.request_blocking('eth_getLogs', [{'topics': []}])
        channel = ChannelInfo(
            sender=event['args']['_sender'],
            receiver=event['args']['_receiver'],
            deposit=event['args']['_deposit'],
            balance=0,
            block=event['blockNumber'],
            balance_proof=None
        )
        self.channels.append(channel)
        self.store_channels()

        return channel

    def create_transfer(self, channel, value):
        assert channel in self.channels

        # TODO: create balance proof
        msg, sig = '3', '4'
        # msg = (value, channel.receiver)
        # sig = ecsign(msg, self.privkey)
        return msg, sig

    def close_channel(self, channel):
        assert channel in self.channels
        tx = self.channel_manager_proxy.create_transaction(
            'close', [channel.receiver, channel.block, channel.balance, channel.balance_proof]
        )
        if not self.dry_run:
            self.web3.eth.sendRawTransaction(tx)

        # TODO: wait for channel close event

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

from collections import namedtuple

from web3 import Web3
from web3.providers.rpc import RPCProvider
from ethereum.utils import privtoaddr, encode_hex, ecsign
import json
import os
import requests

from micropayment.common.contract_proxy import ContractProxy
from micropayment.common.http_header import HTTPHeaders

RESOURCE_BASE_PATH = '/expensive/'
STATUS_OK = 400
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
            if channel['source'] == self.account and channel['target'] == receiver
        ]
        assert len(channels) < 2

        if channels:
            channel = channels[0]
        else:
            channel = self.open_channel(receiver, CHANNEL_SIZE_FACTOR * value)

        return self.create_transfer(channel, value)

    def perform_request(self, resource, balance_proof=None):
        if balance_proof:
            headers = {'RDN-Balance': balance_proof.balance, 'RDN-Balance-Signature': balance_proof.balance_signature}
        else:
            headers = None
        url = 'http://{}:{}{}{}'.format(self.api_endpoint, self.api_port, RESOURCE_BASE_PATH, resource)
        response = requests.get(url, headers=headers)
        return response.status_code, response.headers, response.json()

    def request_resource(self, resource):
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            if headers[HEADERS['CONTRACT']] != self.channel_manager_address:
                print('Invalid channel manager address requested. Aborting.')
                return None

            print('Preparing payment. Price: {}', headers[HEADERS['PRICE']])
            balance_proof = self.perform_payment(headers[HEADERS['RECEIVER']], headers[HEADERS['PRICE']])
            status, headers, body = self.perform_request(resource, balance_proof)

            if status == STATUS_OK:
                print('Resource payment successful. Final cost: {}'.format(headers[HEADERS['COST']]))
            elif status == STATUS_PAYMENT_REQUIRED:
                if HEADERS['INSUF_FUNDS'] in headers:
                    print('Error: Insufficient funds in channel for balance proof.')
                    return None
                elif HEADERS['INSUF_CONFS'] in headers:
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

    def store_channels(self):
        os.makedirs(self.datadir, exist_ok=True)
        with open(os.path.join(self.datadir, CHANNELS_DB), 'w') as channels_file:
            self.channels = json.dump(self.channels, channels_file)

    def open_channel(self, target, deposit):
        tx = self.token_proxy.create_contract_call('approve', [self.channel_manager_address, deposit])
        self.web3.eth.sendRawTransaction(tx)
        tx = self.channel_manager_proxy.create_contract_call('createChannel', [target, deposit], nonce_offset=1)
        self.web3.eth.sendRawTransaction(tx)

        # TODO: await event
        # self.web3._requestManager.request_blocking('eth_getLogs', [{'topics': []}])
        channel = None
        self.store_channels()

        return channel

    def create_transfer(self, channel, value):
        assert channel in self.channels

        msg = (value, channel.receiver)
        sig = ecsign(msg, self.privkey)
        return msg, sig

    def close_channel(self, channel):
        assert channel in self.channels
        tx = self.channel_manager_proxy.create_contract_call(
            'close', [channel.receiver, channel.block, channel.balance, channel.balance_proof]
        )
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

        self.channel_manager_proxy = ContractProxy(
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

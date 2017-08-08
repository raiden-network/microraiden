from collections import namedtuple

from m2mclient.payment_info import PaymentInfo
from web3 import Web3
from web3.providers.rpc import RPCProvider
from ethereum.transactions import Transaction
from ethereum.utils import privtoaddr, encode_hex
import json
import os
import requests

RESOURCE_BASE_PATH = '/expensive/'
STATUS_OK = 400
STATUS_PAYMENT_REQUIRED = 402
CHANNELS_DB = 'channels.json'
GAS_PRICE = 20 * 1000 * 1000 * 1000
GAS_LIMIT = 3141592
CHANNEL_SIZE_FACTOR = 10


ChannelInfo = namedtuple('ChannelInfo', ['source', 'target', 'deposit', 'balance'])
BalanceProof = namedtuple('BalanceProof', ['balance', 'balance_signature'])


class M2MClient(object):
    def perform_payment(self, payment):
        channels = [
            channel for channel in self.channels
            if channel['source'] == self.account and channel['target'] == payment.receiver
        ]
        assert len(channels) < 2

        if channels:
            channel = channels[0]
        else:
            channel = self.open_channel(payment.receiver, CHANNEL_SIZE_FACTOR * payment.price)

        return self.transfer(channel, payment.price)

    def perform_request(self, resource, balance_proof=None):
        if balance_proof:
            headers = {'RDN-Balance': balance_proof.balance, 'RDN-Balance-Signature': balance_proof.balance_signature}
        else:
            headers = None
        url = 'http://{}:{}{}{}'.format(self.api_endpoint, self.api_port, RESOURCE_BASE_PATH, resource)
        response = requests.get(url, headers=headers)
        return response.status_code, PaymentInfo.from_header(response.headers), response.json()

    def request_resource(self, resource):
        status, payment, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            print('Preparing payment. Price: {}', payment.price)
            balance_proof = self.perform_payment(payment)
            status, payment, body = self.perform_request(resource, balance_proof)
            if status == STATUS_OK:
                print('Resource payment successful. Final cost: {}'.format(payment.price))
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
        nonce = self.web3.eth.getTransactionCount(self.account)
        contract = self.web3.eth.contract(self.channel_manager_abi)
        tx = contract._prepare_transaction('getChannel', [self.account, target, self.token_address])

        # TODO: sign, send, await event
        # self.web3._requestManager.request_blocking('eth_getLogs', [{'topics': []}])
        self.store_channels()
        channel = None

        return channel

    def transfer(self, channel, value):
        assert channel in self.channels
        # TODO: perform Raiden transfer to gateway
        balance_proof = None
        return balance_proof

    def close_channel(self, channel):
        assert channel in self.channels
        # TODO: web3 close() on channel contract

    def __init__(
            self,
            api_endpoint,
            api_port,
            datadir,
            rpc_endpoint,
            rpc_port,
            key_path,
            channel_manager_address,
            channel_manager_abi_path,
            token_address
    ):
        self.api_endpoint = api_endpoint
        self.api_port = api_port
        self.datadir = datadir
        self.rpc_endpoint = rpc_endpoint
        self.rpc_port = rpc_port
        self.channel_manager_address = channel_manager_address
        with open(channel_manager_abi_path) as abi_file:
            self.channel_manager_abi = json.load(abi_file)
        self.token_address = token_address
        self.channels = []

        with open(key_path) as keyfile:
            self.privkey = keyfile.readline()[:-1]
        self.account = '0x' + encode_hex(privtoaddr(self.privkey))
        self.rpc = RPCProvider(self.rpc_endpoint, self.rpc_port)
        self.web3 = Web3(self.rpc)

        self.load_channels()

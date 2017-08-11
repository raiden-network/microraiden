import json
import os

import time
import requests
from ethereum.utils import (
    privtoaddr,
    encode_hex,
)
from web3 import Web3
from web3.providers.rpc import RPCProvider

from raiden_mps.client.channel_info import ChannelInfo
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

import logging
log = logging.getLogger(__name__)




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
        self.sync_channels()

    def sync_channels(self):
        created_events = self.channel_manager_proxy.get_channel_created_logs()
        close_requested_events = self.channel_manager_proxy.get_channel_close_requested_logs()
        settled_events = self.channel_manager_proxy.get_channel_settled_logs()

        created_channels = [ChannelInfo.from_event(event, ChannelInfo.State.open) for event in created_events]
        created_channels = [channel for channel in created_channels if channel.sender == self.account]
        settling_channels = [
            ChannelInfo.from_event(event, ChannelInfo.State.settling) for event in close_requested_events
        ]
        settling_channels = [channel for channel in settling_channels if channel.sender == self.account]
        closed_channels = [ChannelInfo.from_event(event, ChannelInfo.State.closed) for event in settled_events]
        closed_channels = [channel for channel in closed_channels if channel.sender == self.account]

        self.channels = ChannelInfo.merge_infos(self.channels, created_channels, settling_channels, closed_channels)
        self.store_channels()

        print('Synced a total of {} channels.'.format(len(self.channels)))

    def load_channels(self):
        channels_path = os.path.join(self.datadir, CHANNELS_DB)
        if not os.path.exists(channels_path):
            return []
        with open(channels_path) as channels_file:
            self.channels = ChannelInfo.from_json(channels_file)

        print('Loaded {} channels from disk.'.format(len(self.channels)))

    def store_channels(self):
        os.makedirs(self.datadir, exist_ok=True)

        with open(os.path.join(self.datadir, CHANNELS_DB), 'w') as channels_file:
            ChannelInfo.to_json(self.channels, channels_file)

    def request_resource(self, resource, tries_max=10):
        channel = None
        for try_n in range(tries_max):
            log.info("getting %s %d/%d", resource, try_n, tries_max)
            status, headers, body = self.perform_request(resource, channel)
#            import pudb;pudb.set_trace()
            if status == STATUS_OK:
                return body
            elif status == STATUS_PAYMENT_REQUIRED:
                if HEADERS['insuf_funds'] in headers:
                    log.error('Error: Insufficient funds in channel for presented balance proof.')
                    continue
                elif HEADERS['insuf_confs'] in headers:
                    log.error(
                        'Error: Newly created channel does not have enough confirmations yet. Waiting for {} more.'
                        .format(headers[HEADERS['insuf_confs']])
                    )
                    time.sleep(9)
                else:
                    channel_manager_address = headers[HEADERS['contract_address']]
                    if channel_manager_address != self.channel_manager_address:
                        log.error('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                        return None

                    price = int(headers[HEADERS['price']])
                    log.debug('Preparing payment of price {}.'.format(price))
                    channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
                    if not channel:
                        raise




    def request_resourceX(self, resource):
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            channel_manager_address = headers[HEADERS['contract_address']]
            if channel_manager_address != self.channel_manager_address:
                log.error('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                return None

            price = int(headers[HEADERS['price']])
            log.error('Preparing payment of price {}.'.format(price))
            channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
            if channel:
                status, headers, body = self.perform_request(resource, channel)

                if status == STATUS_OK:
                    # TODO: use actual cost
                    # print('Resource payment successful. Final cost: {}'.format(headers[HEADERS['cost']]))
                    log.info('Resource payment successful. Final cost: {}'.format(0))
                elif status == STATUS_PAYMENT_REQUIRED:
                    if HEADERS['insuf_funds'] in headers:
                        log.error('Error: Insufficient funds in channel for presented balance proof.')
                    elif HEADERS['insuf_confs'] in headers:
                        log.error(
                            'Error: Newly created channel does not have enough confirmations yet. Waiting for {} more.'
                            .format(headers[HEADERS['insuf_confs']])
                        )
                    else:
                        log.error('Error: Unknown error.')
            else:
                log.error('Error: Could not perform the payment.')

        else:
            log.error('Error code {} while requesting resource: {}'.format(status, body))

    def perform_payment(self, receiver, value):
        channels = [
            channel for channel in self.channels
            if channel.sender.lower() == self.account.lower() and channel.receiver.lower() == receiver.lower() and
               channel.state == ChannelInfo.State.open
        ]
        if len(channels) > 1:
            log.warn('Warning: {} open channels found. Choosing a random one.'.format(len(channels)))

        if channels:
            channel = channels[0]
            log.info('Found open channel, opened at block #{}.'.format(channel.block))
        else:
            deposit = CHANNEL_SIZE_FACTOR * value
            log.info('Creating new channel with deposit {} for receiver {}.'.format(deposit, receiver))
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
        print('Creating channel to {} with an initial deposit of {}.'.format(receiver, deposit))
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

    def close_channel(self, channel, balance=None):
        """If no balance is specified the last stored balance proof will be used."""
        assert channel in self.channels
        print('Closing channel to {} created at block #{}.'.format(channel.receiver, channel.block))
        current_block = self.web3.eth.blockNumber

        if balance:
            channel.balance = 0
            self.create_transfer(channel, balance)
        elif not channel.balance_sig:
            self.create_transfer(channel, 0)

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
            channel.state = ChannelInfo.State.settling
            self.store_channels()
        else:
            print('Error: No event received.')

    def settle_channel(self, channel):
        assert channel.state == ChannelInfo.State.settling
        print('Attempting to settle channel to {} created at block #{}.'.format(channel.receiver, channel.block))

        settle_block = self.channel_manager_proxy.contract.call().getChannelInfo(
            channel.sender, channel.receiver, channel.block
        )[2]

        current_block = self.web3.eth.blockNumber
        wait_remaining = settle_block - current_block
        if wait_remaining > 0:
            print('Warning: {} more blocks until this channel can be settled. Aborting.'.format(wait_remaining))
            return

        tx = self.channel_manager_proxy.create_transaction(
            'settle', [channel.receiver, channel.block]
        )
        if not self.dry_run:
            self.web3.eth.sendRawTransaction(tx)

        print('Waiting for settle confirmation event...')
        event = self.channel_manager_proxy.get_channel_settle_event_blocking(
            channel.sender, channel.receiver, channel.block, current_block + 1
        )

        if event:
            print('Successfully settled channel in block {}.'.format(event['blockNumber']))
            channel.state = ChannelInfo.State.closed
            self.store_channels()
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

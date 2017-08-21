import logging
import time

import requests
from eth_utils import encode_hex

from raiden_mps import Client
from raiden_mps.client.channel import Channel
from raiden_mps.header import HTTPHeaders

STATUS_PAYMENT_REQUIRED = 402
CHANNEL_SIZE_FACTOR = 3
RETRY_INTERVAL = 9
TRIES_MAX = 10
HEADERS = HTTPHeaders.as_dict()

log = logging.getLogger(__name__)


class ChannelCreateError(Exception):
    pass


class InvalidChannelManager(Exception):
    pass


class M2MClient(object):
    def __init__(
            self,
            client: Client,
            api_endpoint,
            api_port,
            initial_deposit=lambda x: x * CHANNEL_SIZE_FACTOR,
            topup_deposit=lambda x: x * CHANNEL_SIZE_FACTOR
    ):
        self.client = client
        self.api_endpoint = api_endpoint
        self.api_port = api_port
        self.channel = None
        self.initial_deposit = initial_deposit
        self.topup_deposit = topup_deposit

    def request_resource(self, resource, tries_max=TRIES_MAX):
        self.channel = None
        for try_n in range(tries_max):
            log.info("getting %s %d/%d", resource, try_n, tries_max)
            status, headers, body = self.perform_request(resource, self.channel)
            if status == requests.codes.OK:
                return status, headers, body
            elif status == requests.codes.PAYMENT_REQUIRED:
                self.handle_payment_request(headers)
            else:
                log.info('OK received.')
                return status, headers, body

    def handle_payment_request(self, headers):
        if HEADERS['insuf_confs'] in headers:
            log.warning(
                'Newly created channel does not have enough confirmations yet. '
                'Waiting for {} more.'.format(headers[HEADERS['insuf_confs']])
            )
            time.sleep(RETRY_INTERVAL)
            return
        else:
            if HEADERS['contract_address'] in headers:
                # Only check if the server actually provides it.
                channel_manager_address = headers[HEADERS['contract_address']]
                if channel_manager_address != self.client.channel_manager_address:
                    raise InvalidChannelManager('Requested: {}'.format(channel_manager_address))
            else:
                log.warning('Server did not specify a contract address. Sending anyway.')

            price = int(headers[HEADERS['price']])
            log.debug('Preparing payment of price {}.'.format(price))
            self.perform_payment(headers[HEADERS['receiver_address']], price)

            if not self.channel:
                raise ChannelCreateError("No channel could be created or sufficiently topped up.")

    def perform_payment(self, receiver, value):
        """
        Attempts to perform a payment on an existing channel or a new one if none is available.
        """
        open_channels = [
            c for c in self.client.channels
            if c.sender.lower() == self.client.account.lower() and
               c.receiver.lower() == receiver.lower() and
               c.state == Channel.State.open
        ]
        suitable_channels = [
            c for c in open_channels if c.deposit - c.balance >= value
        ]
        if len(suitable_channels) > 1:
            log.warning(
                'Warning: {} suitable channels found. Choosing a random one.'
                    .format(len(suitable_channels))
            )

        if suitable_channels:
            # At least one channel with sufficient funds.
            self.channel = suitable_channels[0]
            log.info('Found open channel, opened at block #{}.'.format(self.channel.block))

        elif open_channels:
            # Open channel(s) but insufficient funds. Requires topup.
            log.info('Insufficient funds. Topping up existing channel.')
            channel = max((c.deposit - c.balance, c) for c in open_channels)[1]
            deposit = max(value, self.topup_deposit(value))
            event = channel.topup(deposit)
            self.channel = channel if event else None

        else:
            # No open channels to receiver. Create a new one.
            deposit = max(value, self.initial_deposit(value))
            log.info(
                'Creating new channel with deposit {} for receiver {}.'.format(deposit, receiver)
            )
            self.channel = self.client.open_channel(receiver, deposit)

        if self.channel:
            self.channel.create_transfer(value)

    def perform_request(self, resource, channel=None):
        """
        Performs a simple GET request to the HTTP server with headers representing the given
        channel state.
        """
        if channel:
            headers = {
                HEADERS['contract_address']: self.client.channel_manager_address,
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

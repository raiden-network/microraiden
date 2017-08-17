import logging
import time

import requests
from ethereum.utils import encode_hex

from raiden_mps.client.channel import Channel
from raiden_mps.header import HTTPHeaders

STATUS_PAYMENT_REQUIRED = 402
CHANNEL_SIZE_FACTOR = 3
HEADERS = HTTPHeaders.as_dict()

log = logging.getLogger(__name__)

class ChannelCreateError(Exception):
    pass


class M2MClient(object):
    def __init__(
            self,
            rmp_client,
            api_endpoint,
            api_port
    ):
        self.rmp_client = rmp_client
        self.api_endpoint = api_endpoint
        self.api_port = api_port

    def request_resource(
            self, resource, tries_max=10,
            initial_deposit=lambda x: x * CHANNEL_SIZE_FACTOR,
            topup_deposit=lambda x: x * CHANNEL_SIZE_FACTOR
    ):
        channel = None
        for try_n in range(tries_max):
            log.info("getting %s %d/%d", resource, try_n, tries_max)
            status, headers, body = self.perform_request(resource, channel)
            if status == requests.codes.OK:
                return status, headers, body
            elif status == requests.codes.PAYMENT_REQUIRED:
                if HEADERS['insuf_funds'] in headers:
                    log.error('Error: Insufficient funds in channel for presented balance proof.')
                    continue
                elif HEADERS['insuf_confs'] in headers:
                    log.error(
                        'Error: Newly created channel does not have enough confirmations yet. '
                        'Waiting for {} more.'.format(headers[HEADERS['insuf_confs']])
                    )
                    time.sleep(9)
                else:
                    channel_manager_address = headers[HEADERS['contract_address']]
                    if channel_manager_address != self.rmp_client.channel_manager_address:
                        log.error(
                            'Invalid channel manager address requested ({}). Aborting.'
                            .format(channel_manager_address)
                        )
                        return None

                    price = int(headers[HEADERS['price']])
                    log.debug('Preparing payment of price {}.'.format(price))
                    channel = self.perform_payment(
                        headers[HEADERS['receiver_address']], price,
                        initial_deposit, topup_deposit
                    )
                    if not channel:
                        raise ChannelCreateError("channel couldn't be created")
            else:
                return status, headers, body

    def perform_payment(self, receiver, value, initial_deposit, topup_deposit):
        """
        Attempts to perform a payment on an existing channel or a new one if none is available.
        """
        open_channels = [
            c for c in self.rmp_client.channels
            if c.sender.lower() == self.rmp_client.account.lower() and
               c.receiver.lower() == receiver.lower() and
               c.state == Channel.State.open
        ]
        channels = [
            c for c in open_channels if c.deposit - c.balance >= value
        ]
        if len(channels) > 1:
            log.warning(
                'Warning: {} suitable channels found. Choosing a random one.'.format(len(channels))
            )

        if channels:
            # At least one channel with sufficient funds.
            channel = channels[0]
            log.info('Found open channel, opened at block #{}.'.format(channel.block))

        elif open_channels:
            # Open channel(s) but insufficient funds. Requires topup.
            log.info('Insufficient funds. Topping up existing channel.')
            channel = max((c.deposit - c.balance, c) for c in open_channels)[1]
            deposit = topup_deposit(value)
            event = channel.topup(deposit)
            channel = channel if event else None

        else:
            # No open channels to receiver. Create a new one.
            deposit = initial_deposit(value)
            log.info(
                'Creating new channel with deposit {} for receiver {}.'.format(deposit, receiver)
            )
            channel = self.rmp_client.open_channel(receiver, deposit)

        if channel:
            channel.create_transfer(value)
            return channel
        else:
            return None

    def perform_request(self, resource, channel=None):
        """
        Performs a simple GET request to the HTTP server with headers representing the given
        channel state.
        """
        if channel:
            headers = {
                HEADERS['contract_address']: self.rmp_client.channel_manager_address,
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

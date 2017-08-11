import requests
import time
import logging
from ethereum.utils import encode_hex

from client.channel_info import ChannelInfo
from raiden_mps.header import HTTPHeaders

STATUS_OK = 200
STATUS_PAYMENT_REQUIRED = 402
CHANNEL_SIZE_FACTOR = 3
HEADERS = HTTPHeaders.as_dict()

log = logging.getLogger(__name__)


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
                    if channel_manager_address != self.rmp_client.channel_manager_address:
                        log.error('Invalid channel manager address requested ({}). Aborting.'.format(
                            channel_manager_address))
                        return None

                    price = int(headers[HEADERS['price']])
                    log.debug('Preparing payment of price {}.'.format(price))
                    channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
                    if not channel:
                        raise

    def request_resource_x(self, resource):
        """
        Requests a resource from the HTTP server. Required payment is performed via an existing or a new channel.
        """
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            channel_manager_address = headers[HEADERS['contract_address']]
            if channel_manager_address != self.rmp_client.channel_manager_address:
                log.error('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                return None

            price = int(headers[HEADERS['price']])
            log.error('Preparing payment of price {}.'.format(price))
            channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
            if channel:
                status, headers, body = self.perform_request(resource, channel)

                if status == STATUS_OK:
                    log.info('Resource payment successful. Final cost: {}'.format(headers[HEADERS['cost']]))
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
            print('Error code {} while requesting resource: {}'.format(status, body))

    def perform_payment(self, receiver, value):
        """
        Attempts to perform a payment on an existing channel or a new one if none is available.
        """
        # TODO: topup instead of creation if insufficiently funded.
        channels = [
            channel for channel in self.rmp_client.channels
            if channel.sender.lower() == self.rmp_client.account.lower() and
               channel.receiver.lower() == receiver.lower() and
               channel.state == ChannelInfo.State.open and channel.deposit - channel.balance > value
        ]
        if len(channels) > 1:
            log.warn('Warning: {} open channels found. Choosing a random one.'.format(len(channels)))

        if channels:
            channel = channels[0]
            log.info('Found open channel, opened at block #{}.'.format(channel.block))
        else:
            deposit = CHANNEL_SIZE_FACTOR * value
            log.info('Creating new channel with deposit {} for receiver {}.'.format(deposit, receiver))
            channel = self.rmp_client.open_channel(receiver, deposit)

        if channel:
            self.rmp_client.create_transfer(channel, value)
            return channel
        else:
            return None

    def perform_request(self, resource, channel=None):
        """
        Performs a simple GET request to the HTTP server with headers representing the given channel state.
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

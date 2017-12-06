import logging
from typing import Tuple, Any

import requests
from eth_utils import encode_hex, decode_hex, is_same_address
import json
from munch import Munch
from requests import Response

from microraiden.client import Channel
from microraiden.header import HTTPHeaders
from .client import Client

log = logging.getLogger(__name__)


class HTTPClient(object):
    def __init__(self, client: Client, api_endpoint: str, api_port: int) -> None:
        self.client = client
        self.api_endpoint = api_endpoint
        self.api_port = api_port

        self.channel = None  # type: Channel
        self.running = False
        self.use_ssl = False

    def run(self, requested_resource: str = None):
        self.on_init(requested_resource)
        resource = None
        self.running = True
        retry = True
        while self.running and retry:
            resource, retry = self._request_resource(requested_resource)

        self.on_exit()
        return resource

    def stop(self):
        log.info('Stopping HTTP client.')
        self.running = False

    def make_url(self, resource_path: str):
        # TODO: Do `requests` support other protocols?
        proto = 'https' if self.use_ssl else 'http'
        return '{}://{}:{}/{}'.format(proto, self.api_endpoint, self.api_port, resource_path)

    def close_channel(self, channel: Channel):
        log.info(
            'Requesting closing signature from server for balance {} on channel {}/{}/{}.'
            .format(channel.balance, channel.sender, channel.sender, channel.block)
        )
        url = self.make_url('api/1/channels/{}/{}'.format(channel.sender, channel.block))
        response = requests.delete(url, data={'balance': channel.balance})
        if response.status_code == requests.codes.OK:
            closing_sig = json.loads(response.content.decode())['close_signature']
            channel.close_cooperatively(decode_hex(closing_sig))
        else:
            body = response.content.decode() if response.content else None
            log.error('No closing signature received: {}'.format(body))

    def close_active_channel(self):
        if self.channel:
            self.close_channel(self.channel)

    def _request_resource(self, requested_resource: str) -> Tuple[Any, bool]:
        """
        Performs a simple GET request to the HTTP server with headers representing the given
        channel state.
        """
        headers = Munch()
        headers.contract_address = self.client.channel_manager_address
        if self.channel:
            headers.balance = str(self.channel.balance)
            headers.balance_signature = encode_hex(self.channel.balance_sig)
            headers.sender_address = self.channel.sender
            headers.receiver_address = self.channel.receiver
            headers.open_block = str(self.channel.block)

        url = self.make_url(requested_resource)
        response = requests.get(url, headers=HTTPHeaders.serialize(headers))
        headers = HTTPHeaders.deserialize(response.headers)

        if self.on_http_response(requested_resource, response) is False:
            return None, False  # user requested abort

        if response.status_code == requests.codes.OK:
            return response.content, self.on_success(response.content, headers.get('cost'))

        elif response.status_code == requests.codes.PAYMENT_REQUIRED:
            if 'insuf_confs' in headers:
                return None, self.on_insufficient_confirmations()

            elif 'insuf_funds' in headers:
                return None, self.on_insufficient_funds()

            elif 'contract_address' not in headers or not is_same_address(
                headers.contract_address,
                self.client.channel_manager_address
            ):
                return None, self.on_invalid_contract_address(
                    headers.contract_address
                )

            elif 'invalid_amount' in headers:
                last_balance = None
                if 'sender_balance' in headers:
                    last_balance = int(headers.sender_balance)
                balance_sig = None
                if 'balance_signature' in headers:
                    balance_sig = decode_hex(headers.balance_signature)
                return None, self.on_invalid_amount(int(headers.price), last_balance, balance_sig)

            else:
                return None, self.on_payment_requested(
                    headers.receiver_address,
                    int(headers.price),
                )
        else:
            return None, self.on_http_error(requested_resource, response)

    def on_init(self, requested_resource):
        log.info('Starting request loop for resource at {}.'.format(requested_resource))

    def on_exit(self):
        pass

    def on_success(self, resource, cost: int) -> bool:
        log.info('Resource received.')
        if cost is not None:
            log.info('Final cost was {}.'.format(cost))
        return False

    def on_insufficient_funds(self) -> bool:
        log.error(
            'Server was unable to verify the transfer - Insufficient funds of the balance proof '
            'or possibly an unconfirmed or unregistered topup.'
        )
        return False

    def on_insufficient_confirmations(self) -> bool:
        return True

    def on_invalid_amount(self, price: int, last_balance: int, balance_sig: bytes) -> bool:
        return True

    def on_invalid_contract_address(self, contract_address: str) -> bool:
        log.error(
            'Server sent no or invalid contract address: {}.'.format(contract_address)
        )
        return False

    def on_payment_requested(self, receiver: str, price: int):
        return True

    def on_http_response(self, requested_resource: str, response: Response):
        """Called whenever server returns a reply.
        Return False to abort current request."""
        log.debug('Response received: {}'.format(response.headers))
        return True

    def on_http_error(self, requested_resource: str, response: Response):
        """Triggered under the default behavior when the server returns anything other than a 402
        or 200."""
        log.warning(
            'Unexpected server error, status code {}. Retrying.'.format(response.status_code)
        )
        return True

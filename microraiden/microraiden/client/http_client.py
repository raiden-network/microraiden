import logging
from typing import Tuple, Any

import requests
from eth_utils import encode_hex, decode_hex, is_same_address
from munch import Munch
from requests import Response
from urllib.parse import urlparse

from microraiden.client import Channel
from microraiden.header import HTTPHeaders
from .client import Client

log = logging.getLogger(__name__)


class HTTPClient(object):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.endpoint_to_channel = {}

    def request(self, method: str, url: str, **kwargs) -> Response:
        self.on_init(method, url, **kwargs)
        retry = True
        response = None
        while retry:
            response, retry = self._request_resource(method, url, **kwargs)

        self.on_exit(method, url, response, **kwargs)
        return response

    def head(self, url: str, **kwargs) -> Response:
        return self.request('HEAD', url, **kwargs)

    def get(self, url: str, **kwargs) -> Response:
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        return self.request('PUT', url, **kwargs)

    def patch(self, url: str, **kwargs) -> Response:
        return self.request('PATCH', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        return self.request('DELETE', url, **kwargs)

    @staticmethod
    def get_endpoint(url: str) -> str:
        url_parts = urlparse(url)
        assert url_parts.scheme, 'No protocol scheme specified.'
        return '://'.join(url_parts[:2])

    @staticmethod
    def close_channel(endpoint_url: str, channel: Channel):
        log.debug(
            'Requesting closing signature from server for balance {} on channel {}/{}/{}.'
            .format(channel.balance, channel.sender, channel.sender, channel.block)
        )
        url = '{}/api/1/channels/{}/{}'.format(endpoint_url, channel.sender, channel.block)
        response = requests.delete(url, data={'balance': channel.balance})
        if response.status_code == requests.codes.OK:
            closing_sig = response.json()['close_signature']
            channel.close_cooperatively(decode_hex(closing_sig))
        else:
            log.error('No closing signature received: {}'.format(response.text))

    def get_channel(self, url: str) -> Channel:
        return self.endpoint_to_channel.get(self.get_endpoint(url))

    def set_channel(self, url: str, channel: Channel):
        self.endpoint_to_channel[self.get_endpoint(url)] = channel

    def close_active_channel(self, url: str):
        endpoint = self.get_endpoint(url)
        channel = self.get_channel(url)
        if channel:
            self.close_channel(endpoint, channel)

    def _request_resource(self, method: str, url: str, **kwargs) -> Tuple[Any, bool]:
        """
        Performs a simple GET request to the HTTP server with headers representing the given
        channel state.
        """
        headers = Munch()
        headers.contract_address = self.client.core.channel_manager.address
        channel = self.get_channel(url)
        if channel:
            headers.balance = str(channel.balance)
            headers.balance_signature = encode_hex(channel.balance_sig)
            headers.sender_address = channel.sender
            headers.receiver_address = channel.receiver
            headers.open_block = str(channel.block)

        headers = HTTPHeaders.serialize(headers)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = headers
        response = requests.request(method, url, **kwargs)
        response_headers = HTTPHeaders.deserialize(response.headers)

        if self.on_http_response(method, url, response, **kwargs) is False:
            return None, False  # user requested abort

        if response.status_code == requests.codes.OK:
            return response, self.on_success(method, url, response, **kwargs)

        elif response.status_code == requests.codes.PAYMENT_REQUIRED:
            if 'insuf_confs' in response_headers:
                return None, self.on_insufficient_confirmations(method, url, response, **kwargs)

            elif 'insuf_funds' in response_headers:
                return None, self.on_insufficient_funds(method, url, response, **kwargs)

            elif 'contract_address' not in response_headers or not is_same_address(
                response_headers.contract_address,
                self.client.core.channel_manager.address
            ):
                return None, self.on_invalid_contract_address(method, url, response, **kwargs)

            elif 'invalid_amount' in response_headers:
                return None, self.on_invalid_amount(method, url, response, **kwargs)

            else:
                return None, self.on_payment_requested(method, url, response, **kwargs)
        else:
            return None, self.on_http_error(method, url, response, **kwargs)

    def on_init(self, method: str, url: str, **kwargs):
        log.debug('Starting {} request loop for resource at {}.'.format(method, url))

    def on_exit(self, method: str, url: str, response: Response, **kwargs):
        pass

    def on_success(self, method: str, url: str, response: Response, **kwargs) -> bool:
        log.debug('Resource received.')
        cost = response.headers.get(HTTPHeaders.COST)
        if cost is not None:
            log.debug('Final cost was {}.'.format(cost))
        return False

    def on_insufficient_funds(self, method: str, url: str, response: Response, **kwargs) -> bool:
        log.error(
            'Server was unable to verify the transfer - Insufficient funds of the balance proof '
            'or possibly an unconfirmed or unregistered topup.'
        )
        return False

    def on_insufficient_confirmations(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        return True

    def on_invalid_amount(self, method: str, url: str, response: Response, **kwargs) -> bool:
        return True

    def on_invalid_contract_address(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        contract_address = response.headers.get(HTTPHeaders.CONTRACT_ADDRESS)
        log.error(
            'Server sent no or invalid contract address: {}.'.format(contract_address)
        )
        return False

    def on_payment_requested(self, method: str, url: str, response: Response, **kwargs):
        return True

    def on_http_response(self, method: str, url: str, response: Response, **kwargs):
        """Called whenever server returns a reply.
        Return False to abort current request."""
        log.debug('Response received: {}'.format(response.headers))
        return True

    def on_http_error(self, method: str, url: str, response: Response, **kwargs):
        """Triggered under the default behavior when the server returns anything other than a 402
        or 200."""
        return False

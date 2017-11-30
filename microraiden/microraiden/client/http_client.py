import logging

import requests
from eth_utils import encode_hex, decode_hex
import json
from munch import Munch

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

    def run(self, requested_resource=None):
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

    def _request_resource(self, requested_resource: str):
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

        if response.status_code == requests.codes.OK:
            self.on_success(response.content, headers.get('cost'))
            return response.content, False
        elif response.status_code == requests.codes.PAYMENT_REQUIRED:
            if 'insuf_confs' in headers:
                self.on_insufficient_confirmations()
            elif 'insuf_funds' in headers:
                self.on_insufficient_funds()
            elif 'invalid_amount' in headers:
                self.on_invalid_amount()
                self.channel.balance = int(headers.sender_balance)
                return None, False
            else:
                balance = int(headers.sender_balance) if 'sender_balance' in headers else None
                balance_sig = decode_hex(headers.balance_signature) \
                    if 'balance_signature' in headers else None
                self.on_payment_requested(
                    headers.receiver_address,
                    int(headers.price),
                    balance,
                    balance_sig,
                    headers.get('contract_address')
                )
            return None, True

    def on_init(self):
        pass

    def on_exit(self):
        pass

    def on_success(self, resource, cost: int):
        pass

    def on_insufficient_funds(self):
        pass

    def on_insufficient_confirmations(self):
        pass

    def on_invalid_amount(self):
        pass

    def on_payment_requested(
            self,
            receiver: str,
            price: int,
            balance: int,
            balance_sig: bytes,
            channel_manager_address: str
    ):
        pass

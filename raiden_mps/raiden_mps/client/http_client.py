import requests
from eth_utils import encode_hex, decode_hex
from munch import Munch

from raiden_mps.header import HTTPHeaders
from .client import Client


class HTTPClient(object):
    def __init__(self, client: Client, api_endpoint, api_port):
        self.client = client
        self.api_endpoint = api_endpoint
        self.api_port = api_port

        self.channel = None
        self.requested_resource = None
        self.retry = False

    def run(self, requested_resource=None):
        if requested_resource:
            self.requested_resource = requested_resource
        self.on_init()
        resource = None
        self.retry = True
        while self.retry and self.requested_resource:
            self.retry = False
            resource = self._request_resource()

        self.on_exit()
        return resource

    def _request_resource(self):
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

        url = 'http://{}:{}/{}'.format(self.api_endpoint, self.api_port, self.requested_resource)
        response = requests.get(url, headers=HTTPHeaders.serialize(headers))
        headers = HTTPHeaders.deserialize(response.headers)

        if response.status_code == requests.codes.OK:
            self.on_success(response.content, headers.get('cost'))
            return response.content
        elif response.status_code == requests.codes.PAYMENT_REQUIRED:
            if 'insuf_confs' in headers:
                self.on_insufficient_confirmations()
            elif 'insuf_funds' in headers:
                self.on_insufficient_funds()
            else:
                balance = int(headers.get('sender_balance', 0))
                if 'balance_signature' in headers:
                    balance_sig = decode_hex(headers.balance_signature)
                else:
                    balance_sig = None
                if self.approve_payment(
                    headers.receiver_address,
                    int(headers.price),
                    balance,
                    balance_sig,
                    headers.get('contract_address')
                ):
                    self.on_payment_approved(headers.receiver_address, int(headers.price))

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

    def approve_payment(
            self,
            receiver: str,
            price: int,
            balance: int,
            balance_sig: bytes,
            channel_manager_address: str
    ) -> bool:
        return False

    def on_payment_approved(self, receiver: str, price: int):
        pass

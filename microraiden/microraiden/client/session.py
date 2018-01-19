import logging
import time
from typing import Callable, Tuple, Union

import requests
from eth_utils import is_same_address, decode_hex, encode_hex
from munch import Munch
from requests import Response

from microraiden.header import HTTPHeaders
from microraiden.client import Client, Channel
from microraiden.utils import verify_balance_proof

log = logging.getLogger(__name__)


class Session(requests.Session):
    def __init__(
            self,
            client: Client = None,
            endpoint_url: str = None,
            retry_interval: float = 5,
            initial_deposit: Callable[[int], int] = lambda price: 10 * price,
            topup_deposit: Callable[[int], int] = lambda price: 5 * price,
            close_channel_on_exit: bool = False,
            **client_kwargs
    ) -> None:
        requests.Session.__init__(self)
        self.channel = None  # type: Channel
        self.endpoint_url = endpoint_url
        self.client = client
        self.retry_interval = retry_interval
        self.initial_deposit = initial_deposit
        self.topup_deposit = topup_deposit
        self.close_channel_on_exit = close_channel_on_exit

        if self.client is None:
            self.client = Client(**client_kwargs)

    def close(self):
        if self.close_channel_on_exit and self.channel.state == Channel.State.open:
            self.close_channel()
        requests.Session.close(self)

    def request(self, method: str, url: str, **kwargs) -> Response:
        self.on_init(method, url, **kwargs)
        retry = True
        response = None
        while retry:
            response, retry = self._request_resource(method, url, **kwargs)

        self.on_exit(method, url, response, **kwargs)
        return response

    def close_channel(self, endpoint_url: str = None):
        if self.channel is None:
            log.debug('No channel to close.')
            return

        if endpoint_url is None:
            endpoint_url = self.endpoint_url

        if endpoint_url is None:
            log.warning('No endpoint URL specified to request a closing signature.')
            self.on_cooperative_close_denied()
            return

        log.debug(
            'Requesting closing signature from server for balance {} on channel {}/{}/{}.'
            .format(
                self.channel.balance,
                self.channel.sender,
                self.channel.sender,
                self.channel.block
            )
        )
        url = '{}/api/1/channels/{}/{}'.format(
            endpoint_url,
            self.channel.sender,
            self.channel.block
        )

        # We need to call request directly because delete would perform a uRaiden request.
        try:
            response = requests.Session.request(
                self,
                'DELETE',
                url,
                data={'balance': self.channel.balance}
            )
        except requests.exceptions.ConnectionError as err:
            log.error(
                'Could not get a response from the server while requesting a closing signature: {}'
                .format(err)
            )
            response = None

        failed = True
        if response is not None and response.status_code == requests.codes.OK:
            closing_sig = response.json()['close_signature']
            failed = self.channel.close_cooperatively(decode_hex(closing_sig)) is None

        if response is None or failed:
            self.on_cooperative_close_denied(response)

    def _request_resource(
            self,
            method: str,
            url: str,
            **kwargs
    ) -> Tuple[Union[None, Response], bool]:
        """
        Performs a simple GET request to the HTTP server with headers representing the given
        channel state.
        """
        headers = Munch()
        headers.contract_address = self.client.context.channel_manager.address
        if self.channel is not None:
            headers.balance = str(self.channel.balance)
            headers.balance_signature = encode_hex(self.channel.balance_sig)
            headers.sender_address = self.channel.sender
            headers.receiver_address = self.channel.receiver
            headers.open_block = str(self.channel.block)

        headers = HTTPHeaders.serialize(headers)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = headers
        response = requests.Session.request(self, method, url, **kwargs)

        if self.on_http_response(method, url, response, **kwargs) is False:
            return response, False  # user requested abort

        if response.status_code == requests.codes.OK:
            return response, self.on_success(method, url, response, **kwargs)

        elif response.status_code == requests.codes.PAYMENT_REQUIRED:
            if HTTPHeaders.NONEXISTING_CHANNEL in response.headers:
                return response, self.on_nonexisting_channel(method, url, response, **kwargs)

            elif HTTPHeaders.INSUF_CONFS in response.headers:
                return response, self.on_insufficient_confirmations(
                    method,
                    url,
                    response,
                    **kwargs
                )

            elif HTTPHeaders.INVALID_PROOF in response.headers:
                return response, self.on_invalid_balance_proof(method, url, response, **kwargs)

            elif HTTPHeaders.CONTRACT_ADDRESS not in response.headers or not is_same_address(
                response.headers.get(HTTPHeaders.CONTRACT_ADDRESS),
                self.client.context.channel_manager.address
            ):
                return response, self.on_invalid_contract_address(method, url, response, **kwargs)

            elif HTTPHeaders.INVALID_AMOUNT in response.headers:
                return response, self.on_invalid_amount(method, url, response, **kwargs)

            else:
                return response, self.on_payment_requested(method, url, response, **kwargs)
        else:
            return response, self.on_http_error(method, url, response, **kwargs)

    def on_nonexisting_channel(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        log.warning(
            'Channel not registered by server. Retrying in {} seconds.'
            .format(self.retry_interval)
        )
        time.sleep(self.retry_interval)
        return True

    def on_insufficient_confirmations(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        log.warning(
            'Newly created channel does not have enough confirmations yet. Retrying in {} seconds.'
            .format(self.retry_interval)
        )
        time.sleep(self.retry_interval)
        return True

    def on_invalid_balance_proof(
        self,
        method: str,
        url: str,
        response: Response,
        **kwargs
    ) -> bool:
        log.warning(
            'Server was unable to verify the transfer - '
            'Either the balance was greater than deposit'
            'or the balance proof contained a lower balance than expected'
            'or possibly an unconfirmed or unregistered topup. Retrying in {} seconds.'
        )
        time.sleep(self.retry_interval)
        return True

    def on_invalid_amount(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        log.debug('Server claims an invalid amount sent.')
        balance_sig = response.headers.get(HTTPHeaders.BALANCE_SIGNATURE)
        if balance_sig:
            balance_sig = decode_hex(balance_sig)
        last_balance = int(response.headers.get(HTTPHeaders.SENDER_BALANCE))

        verified = balance_sig and is_same_address(
            verify_balance_proof(
                self.channel.receiver,
                self.channel.block,
                last_balance,
                balance_sig,
                self.client.context.channel_manager.address
            ),
            self.channel.sender
        )

        if verified:
            if last_balance == self.channel.balance:
                log.error(
                    'Server tried to disguise the last unconfirmed payment as a confirmed payment.'
                )
                return False
            else:
                log.debug(
                    'Server provided proof for a different channel balance ({}). Adopting.'.format(
                        last_balance
                    )
                )
                self.channel.update_balance(last_balance)
        else:
            log.debug(
                'Server did not provide proof for a different channel balance. Reverting to 0.'
            )
            self.channel.update_balance(0)

        return self.on_payment_requested(method, url, response, **kwargs)

    def on_payment_requested(
            self,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ) -> bool:
        receiver = response.headers[HTTPHeaders.RECEIVER_ADDRESS]
        price = int(response.headers[HTTPHeaders.PRICE])
        assert price > 0

        log.debug('Preparing payment of price {} to {}.'.format(price, receiver))

        if self.channel is None or self.channel.state != Channel.State.open:
            new_channel = self.client.get_suitable_channel(
                receiver, price, self.initial_deposit, self.topup_deposit
            )

            if self.channel is not None and new_channel != self.channel:
                # This should only happen if there are multiple open channels to the target or a
                # channel has been closed while the session is still being used.
                log.warning(
                    'Channels switched. Previous balance proofs not applicable to new channel.'
                )

            self.channel = new_channel
        elif not self.channel.is_suitable(price):
            self.channel.topup(self.topup_deposit(price))

        if self.channel is None:
            log.error("No channel could be created or sufficiently topped up.")
            return False

        self.channel.create_transfer(price)
        log.debug(
            'Sending new balance proof. New channel balance: {}/{}'
            .format(self.channel.balance, self.channel.deposit)
        )

        return True

    def on_http_error(self, method: str, url: str, response: Response, **kwargs) -> bool:
        log.error(
            'Unexpected server error, status code {}'.format(response.status_code)
        )
        return False

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

    def on_cooperative_close_denied(self, response: Response = None):
        log.warning(
            'No valid closing signature received. Closing noncooperatively on a balance of 0.'
        )
        self.channel.close(0)

    def on_http_response(self, method: str, url: str, response: Response, **kwargs) -> bool:
        """Called whenever server returns a reply.
        Return False to abort current request."""
        log.debug('Response received: {}'.format(response.headers))
        return True

import logging
import time
from typing import Callable

from eth_utils import is_same_address, decode_hex
from requests import Response

from microraiden.header import HTTPHeaders
from microraiden.client import Client
from microraiden.utils import verify_balance_proof
from .http_client import HTTPClient

log = logging.getLogger(__name__)


class DefaultHTTPClient(HTTPClient):
    def __init__(
            self,
            client: Client,
            retry_interval: float = 5,
            initial_deposit: Callable[[int], int] = lambda price: 10 * price,
            topup_deposit: Callable[[int], int] = lambda price: 5 * price
    ) -> None:
        HTTPClient.__init__(self, client)
        self.retry_interval = retry_interval
        self.initial_deposit = initial_deposit
        self.topup_deposit = topup_deposit

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

        channel = self.get_channel(url)
        verified = balance_sig and is_same_address(
            verify_balance_proof(
                channel.receiver,
                channel.block,
                last_balance,
                balance_sig,
                self.client.core.channel_manager.address
            ),
            channel.sender
        )

        if verified:
            if last_balance == channel.balance:
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
                channel.update_balance(last_balance)
        else:
            log.debug(
                'Server did not provide proof for a different channel balance. Reverting to 0.'
            )
            channel.update_balance(0)

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

        channel = self.get_channel(url)
        if not channel or not channel.is_suitable(price):
            new_channel = self.client.get_suitable_channel(
                receiver, price, self.initial_deposit, self.topup_deposit
            )

            if channel and new_channel != channel:
                # This should only happen if there are multiple open channels to the target.
                log.warning(
                    'Channels switched. Previous balance proofs not applicable to new channel.'
                )

            channel = new_channel
            self.set_channel(url, channel)

        if not channel:
            log.error("No channel could be created or sufficiently topped up.")
            return False

        channel.create_transfer(price)
        log.debug(
            'Sending new balance proof. New channel balance: {}/{}'
            .format(channel.balance, channel.deposit)
        )

        return True

    def on_http_error(self, method: str, url: str, response: Response, **kwargs):
        log.warning(
            'Unexpected server error, status code {}. Retrying in {} seconds.'.format(
                response.status_code, self.retry_interval
            )
        )
        time.sleep(self.retry_interval)
        return True

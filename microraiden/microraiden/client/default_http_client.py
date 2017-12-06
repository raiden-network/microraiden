import logging
import time
from typing import Callable

from eth_utils import is_same_address

from microraiden.client import Channel, Client
from microraiden.crypto import verify_balance_proof
from .http_client import HTTPClient

log = logging.getLogger(__name__)


class DefaultHTTPClient(HTTPClient):
    def __init__(
            self,
            client: Client,
            api_endpoint: str,
            api_port: int,
            retry_interval: float = 5,
            initial_deposit: Callable[[int], int] = lambda price: 10 * price,
            topup_deposit: Callable[[int], int] = lambda price: 5 * price
    ) -> None:
        super().__init__(client, api_endpoint, api_port)
        self.retry_interval = retry_interval
        self.initial_deposit = initial_deposit
        self.topup_deposit = topup_deposit
        self.channel = None  # type: Channel

    def on_insufficient_confirmations(self) -> bool:
        log.warning(
            'Newly created channel does not have enough confirmations yet. Retrying in {} seconds.'
            .format(self.retry_interval)
        )
        time.sleep(self.retry_interval)
        return True

    def on_invalid_amount(self, price: int, last_balance: int, balance_sig: bytes) -> bool:
        log.info('Server claims an invalid amount sent.')

        verified = balance_sig and is_same_address(
            verify_balance_proof(
                self.channel.receiver,
                self.channel.block,
                last_balance,
                balance_sig,
                self.client.channel_manager_address
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
                log.info(
                    'Server provided proof for a different channel balance ({}). Adopting.'.format(
                        last_balance
                    )
                )
                self.channel.balance = last_balance
        else:
            log.info(
                'Server did not provide proof for a different channel balance. Reverting to 0.'
            )
            self.channel.balance = 0

        return self.on_payment_requested(self.channel.receiver, price)

    def on_payment_requested(self, receiver: str, price: int) -> bool:
        assert price > 0

        log.info('Preparing payment of price {} to {}.'.format(price, receiver))

        if not self.channel or not self.channel.is_suitable(price):
            channel = self.client.get_suitable_channel(
                receiver, price, self.initial_deposit, self.topup_deposit
            )

            if self.channel and channel != self.channel:
                # This should only happen if there are multiple open channels to the target.
                log.warning(
                    'Channels switched. Previous balance proofs not applicable to new channel.'
                )

            self.channel = channel

        if not self.channel:
            log.error("No channel could be created or sufficiently topped up.")
            return False

        self.channel.create_transfer(price)
        log.info(
            'Sending new balance proof. New channel balance: {}/{}'
            .format(self.channel.balance, self.channel.deposit)
        )

        return True

    @staticmethod
    def is_suitable_channel(channel: Channel, receiver: str, value: int):
        return (channel.deposit - channel.balance >= value and
                is_same_address(channel.receiver, receiver))

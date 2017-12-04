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

    def on_init(self, requested_resource: str):
        log.info('Starting request loop for resource at {}.'.format(requested_resource))

    def on_success(self, resource, cost: int):
        log.info('Resource received.')
        if cost:
            log.info('Final cost was {}.'.format(cost))

    def on_insufficient_confirmations(self) -> bool:
        log.warning(
            'Newly created channel does not have enough confirmations yet. Retrying in {} seconds.'
            .format(self.retry_interval)
        )
        time.sleep(self.retry_interval)
        return True

    def on_insufficient_funds(self) -> bool:
        log.error(
            'Server was unable to verify the transfer - Insufficient funds of the balance proof.'
        )
        return False

    def on_invalid_amount(self) -> bool:
        log.error(
            'Server was unable to verify the transfer - Invalid amount sent by the client.'
        )
        return True

    def _approve_payment(self, balance: int, balance_sig: bytes, channel_manager_address: str):
        assert balance is None or isinstance(balance, int)
        if not channel_manager_address:
            log.warning('Server did not specify a contract address.')
        elif not is_same_address(channel_manager_address, self.client.channel_manager_address):
            log.error(
                'Server requested invalid channel manager: {}'.format(channel_manager_address)
            )
            return False

        return self._sync_balance(balance, balance_sig)

    def _sync_balance(self, balance: int, balance_sig: bytes) -> bool:
        if not self.channel:
            # Nothing to verify or sync. Server does not know about a channel yet.
            return True
        elif balance is None:
            # Server does know about the channel but cannot confirm its creation yet.
            log.info(
                'Server could not confirm new channel yet. Waiting for {} seconds.'
                .format(self.retry_interval)
            )
            time.sleep(self.retry_interval)
            return True

        verified = balance_sig and is_same_address(
            verify_balance_proof(
                self.channel.receiver,
                self.channel.block,
                balance,
                balance_sig,
                self.client.channel_manager_address
            ),
            self.channel.sender
        )

        if balance > self.channel.balance:
            if verified:
                log.info(
                    'Server proved a higher channel balance (server/local): {}/{}. Adopting.'
                    .format(balance, self.channel.balance)
                )
                self.channel.balance = balance
            else:
                log.error(
                    'Server could not prove higher channel balance (server/local): {}/{}'
                    .format(balance, self.channel.balance)
                )
                return False

        elif balance < self.channel.balance:
            if verified:
                log.info(
                    'Server sent older balance proof or rejected the last one (server/local): '
                    '{}/{}. Possibly because of an unconfirmed topup. Retrying in {} seconds.'
                    .format(balance, self.channel.balance, self.retry_interval)
                )
                self.channel.balance = balance

                time.sleep(self.retry_interval)
            else:
                log.info(
                    'Server sent lower balance without proof. Attempting to continue on lower '
                    'balance (server/local): {}.'.format(balance, self.channel.balance)
                )
                self.channel.balance = balance

        return True

    def on_payment_requested(
            self,
            receiver: str,
            price: int,
            balance: int,
            balance_sig: bytes,
            channel_manager_address: str
    ) -> bool:
        if not self._approve_payment(balance, balance_sig, channel_manager_address):
            return False

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

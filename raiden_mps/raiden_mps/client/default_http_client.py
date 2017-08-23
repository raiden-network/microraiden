import logging
import time
from typing import Callable

from eth_utils import is_same_address

from raiden_mps.client import Channel
from raiden_mps.crypto import verify_balance_proof
from .http_client import HTTPClient

log = logging.getLogger(__name__)


class DefaultHTTPClient(HTTPClient):
    def __init__(
            self,
            client,
            api_endpoint,
            api_port,
            retry_interval: float = 5,
            initial_deposit: Callable[[int], int] = lambda price: 10 * price,
            topup_deposit: Callable[[int], int] = lambda price: 5 * price
    ):
        super().__init__(client, api_endpoint, api_port)
        self.retry_interval = retry_interval
        self.initial_deposit = initial_deposit
        self.topup_deposit = topup_deposit

    def on_init(self):
        if self.requested_resource:
            log.info('Starting request loop for resource at {}.'.format(self.requested_resource))
        else:
            log.info('No resource specified.')

    def on_success(self, resource, cost: int):
        log.info('Resource received.')
        if cost:
            log.info('Final cost was {}.'.format(cost))

    def on_insufficient_confirmations(self):
        log.warning(
            'Newly created channel does not have enough confirmations yet. Retrying in {} seconds.'
                .format(self.retry_interval)
        )
        time.sleep(self.retry_interval)
        self.retry = True

    def on_insufficient_funds(self):
        log.error('Server was unable to verify the transfer.')

    def approve_payment(
            self,
            receiver: str,
            price: int,
            balance: int,
            balance_sig: bytes,
            channel_manager_address: str
    ) -> bool:
        if not channel_manager_address:
            log.warning('Server did not specify a contract address.')
        elif not is_same_address(channel_manager_address, self.client.channel_manager_address):
            log.error(
                'Server requested invalid channel manager: {}'.format(channel_manager_address)
            )
            return False

        if self.channel:
            if balance > self.channel.balance:
                if balance_sig and self.channel.sender == verify_balance_proof(
                        self.channel.receiver, self.channel.block, balance, balance_sig,
                        self.client.channel_manager_address
                ):
                    log.info(
                        'Server proved a higher channel balance (server/local): {}/{}. Adopting.'
                        .format(balance, self.channel.balance)
                    )
                    self.channel.balance = balance
                    self.channel.balance_sig = balance_sig
                else:
                    log.error(
                        'Server could not prove higher channel balance (server/local): {}/{}'
                            .format(balance, self.channel.balance)
                    )
                    return False

            elif balance < self.channel.balance:
                if balance_sig and self.channel.sender == verify_balance_proof(
                        self.channel.receiver, self.channel.block, balance, balance_sig,
                        self.client.channel_manager_address
                ):
                    # Free money.
                    log.info(
                        'Server sent older balance proof or rejected the last one (server/local): '
                        '{}/{}. Retrying in {} seconds.'
                        .format(balance, self.channel.balance, self.retry_interval)
                    )
                    self.channel.balance = balance
                    self.channel.balance_sig = balance_sig

                    time.sleep(self.retry_interval)
                    self.retry = True
                    return False
                else:
                    log.info(
                        'Server sent lower balance without proof. Attempting to continue on lower '
                        'balance (server/local): {}.'.format(balance, self.channel.balance)
                    )
                    self.channel.balance = balance
                    self.channel.create_transfer(0)

                    return True

        return True

    def on_payment_approved(self, receiver: str, price: int):
        assert price > 0

        log.info('Preparing payment of price {} to {}.'.format(price, receiver))

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
            return

        self.channel.create_transfer(price)
        log.info(
            'Sending new balance proof. New channel balance: {}/{}'
            .format(self.channel.balance, self.channel.deposit)
        )
        self.retry = True

    @staticmethod
    def is_suitable_channel(channel: Channel, receiver: str, value: int):
        return channel.deposit - channel.balance >= value and \
               is_same_address(channel.receiver, receiver)

import logging
import time
from typing import Callable

from raiden_mps.client import Channel
from raiden_mps.crypto import equal_addrs
from .http_client import HTTPClient

log = logging.getLogger(__name__)


class DefaultHTTPClient(HTTPClient):
    def __init__(
            self,
            client,
            api_endpoint,
            api_port,
            retry_interval: int = 5,
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

    def on_exit(self):
        log.info('Exiting.')

    def on_success(self, resource, cost: int):
        log.info('Successfully requested resource.')
        if cost:
            log.info('Final cost was {}.'.format(cost))

    def on_payment_requested(
            self, receiver: str, price: int, confirmed_balance: int, channel_manager_address: str
    ):
        if not channel_manager_address:
            log.warning('Server did not specify a contract address. Paying anyway.')
        elif not equal_addrs(channel_manager_address, self.client.channel_manager_address):
            log.error(
                'Server requested invalid channel manager: {}'.format(channel_manager_address)
            )
            return

        if self.channel:
            price -= self.channel.balance - confirmed_balance

        if price == 0:
            log.info(
                'Requested amount already paid. Retrying payment in {} seconds.'
                    .format(self.retry_interval)
            )
            time.sleep(self.retry_interval)
            self.retry = True
            return

        assert price > 0

        log.info('Preparing payment of price {} to {}.'.format(price, receiver))

        if not self.channel or not self.is_suitable_channel(self.channel, receiver, price):
            open_channels = [
                c for c in self.client.channels
                if equal_addrs(c.sender, self.client.account.lower()) and
                   equal_addrs(c.receiver, receiver) and
                   c.state == Channel.State.open
            ]
            suitable_channels = [
                c for c in open_channels if c.deposit - c.balance >= price
            ]

            if len(suitable_channels) > 1:
                log.warning(
                    'Warning: {} suitable channels found. Choosing a random one.'
                        .format(len(suitable_channels))
                )

            if suitable_channels:
                # At least one channel with sufficient funds.
                self.channel = suitable_channels[0]
                log.info(
                    'Found suitable open channel, opened at block #{}.'.format(self.channel.block)
                )

            elif open_channels:
                # Open channel(s) but insufficient funds. Requires topup.
                log.info('Insufficient funds. Topping up existing channel.')
                channel = max((c.deposit - c.balance, c) for c in open_channels)[1]
                deposit = max(price, self.topup_deposit(price))
                event = channel.topup(deposit)
                self.channel = channel if event else None

            else:
                # No open channels to receiver. Create a new one.
                deposit = max(price, self.initial_deposit(price))
                log.info('Creating new channel with deposit {}.'.format(deposit))
                self.channel = self.client.open_channel(receiver, deposit)

        if not self.channel:
            log.error("No channel could be created or sufficiently topped up.")
            return

        self.channel.create_transfer(price)
        self.retry = True

    def on_insufficient_confirmations(self, pending_confirmations: int):
        log.warning(
            'Newly created channel does not have enough confirmations yet. '
            'Waiting for {} more. Retrying in {} seconds.'
                .format(pending_confirmations, self.retry_interval)
        )
        time.sleep(self.retry_interval)
        self.retry = True

    def on_insufficient_funds(self):
        log.error('Server was unable to verify the transfer.')

    @staticmethod
    def is_suitable_channel(channel: Channel, receiver: str, value: int):
        return channel.deposit - channel.balance >= value and \
               equal_addrs(channel.receiver, receiver)


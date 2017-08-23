import logging

import pytest

from raiden_mps import DefaultHTTPClient
from raiden_mps.examples.eth_ticker import ETHTicker
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy


def test_eth_ticker(
        doggo_proxy: PaywalledProxy,
        default_http_client: DefaultHTTPClient,
        sender_privkey: str,
        clean_channels
):
    logging.basicConfig(level=logging.INFO)

    ticker = ETHTicker(sender_privkey, proxy=doggo_proxy, httpclient=default_http_client)

    def post():
        ticker.close()

        # This test fails if ETH price is below 100 USD. But why even bother anymore if it does?
        assert float(ticker.pricevar.get().split()[0]) > 100
        client = default_http_client.client
        assert len(client.get_open_channels()) == 0

    ticker.root.after(6000, post)
    ticker.run()

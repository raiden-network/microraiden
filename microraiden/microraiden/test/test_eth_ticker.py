import logging

import pytest  # noqa: F401

from microraiden import DefaultHTTPClient
from microraiden.examples.eth_ticker import ETHTickerClient, ETHTickerProxy
from microraiden.proxy.paywalled_proxy import PaywalledProxy


@pytest.mark.needs_xorg
def test_eth_ticker(
        doggo_proxy: PaywalledProxy,
        default_http_client: DefaultHTTPClient,
        sender_privkey: str,
        receiver_privkey: str,
):
    logging.basicConfig(level=logging.INFO)

    proxy = ETHTickerProxy(receiver_privkey, proxy=doggo_proxy)
    ticker = ETHTickerClient(sender_privkey, httpclient=default_http_client)

    def post():
        ticker.close()
        proxy.stop()

        # This test fails if ETH price is below 100 USD. But why even bother anymore if it does?
        assert float(ticker.pricevar.get().split()[0]) > 100
        client = default_http_client.client
        assert len(client.get_open_channels()) == 0

    ticker.root.after(6000, post)
    ticker.run()

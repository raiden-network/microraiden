import pytest  # noqa: F401
from _pytest.monkeypatch import MonkeyPatch
from flask import jsonify

from microraiden import DefaultHTTPClient
from microraiden.examples.eth_ticker import ETHTickerClient, ETHTickerProxy
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.proxy.resources import PaywalledProxyUrl


@pytest.mark.needs_xorg
def test_eth_ticker(
        empty_proxy: PaywalledProxy,
        default_http_client: DefaultHTTPClient,
        sender_privkey: str,
        receiver_privkey: str,
        monkeypatch: MonkeyPatch
):
    def get_patched(*args, **kwargs):
        body = {
            'mid': '682.435', 'bid': '682.18', 'ask': '682.69', 'last_price': '683.16',
            'low': '532.97', 'high': '684.0', 'volume': '724266.25906224',
            'timestamp': '1513167820.721733'
        }
        return jsonify(body)

    monkeypatch.setattr(PaywalledProxyUrl, 'get', get_patched)

    ETHTickerProxy(receiver_privkey, proxy=empty_proxy)
    ticker = ETHTickerClient(sender_privkey, httpclient=default_http_client, poll_interval=0.5)

    def post():
        ticker.close()

        assert ticker.pricevar.get() == '683.16 USD'
        client = default_http_client.client
        assert len(client.get_open_channels()) == 0
        ticker.success = True

    ticker.success = False
    ticker.root.after(1500, post)
    ticker.run()
    assert ticker.success

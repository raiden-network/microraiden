import pytest  # noqa: F401
from _pytest.monkeypatch import MonkeyPatch
from flask import jsonify
from web3 import Web3
import os

from microraiden import Session
from microraiden.channel_manager import ChannelManager
from microraiden.examples.ticker_proxy import ETHTickerProxy
from microraiden.examples.ticker_client import ETHTickerClient
from microraiden.examples.echo_server import run as run_echo_server
from microraiden.examples.echo_client import run as run_echo_client
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.proxy.resources import PaywalledProxyUrl
import microraiden.client.session


@pytest.mark.skipif(
    ('TEST_SKIP_XORG' in os.environ),
    reason='requires Xorg'
)
def test_eth_ticker(
        empty_proxy: PaywalledProxy,
        session: Session,
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
    ticker = ETHTickerClient(sender_privkey, session=session, poll_interval=0.5)

    def post():
        ticker.close()

        assert ticker.pricevar.get() == '683.16 USD'
        assert len(session.client.get_open_channels()) == 0
        ticker.success = True

    session.close_channel_on_exit = True
    ticker.success = False
    ticker.root.after(1500, post)
    ticker.run()
    assert ticker.success


def patch_session(web3, monkeypatch):
    # If a channel creation transaction has not been mined yet or the server demands more
    # confirmations, simply mine some more blocks on the tester chain.
    on_nonexisting_channel_original = Session.on_nonexisting_channel

    def on_nonexisting_channel_patched(self, *args, **kwargs):
        web3.testing.mine(6)
        return on_nonexisting_channel_original(self, *args, **kwargs)

    on_insufficient_confirmations_original = Session.on_insufficient_confirmations

    def on_insufficient_confirmations_patched(self, *args, **kwargs):
        web3.testing.mine(6)
        return on_insufficient_confirmations_original(self, *args, **kwargs)

    monkeypatch.setattr(
        microraiden.client.session.Session,
        'on_nonexisting_channel',
        on_nonexisting_channel_patched
    )

    monkeypatch.setattr(
        microraiden.client.session.Session,
        'on_insufficient_confirmations',
        on_insufficient_confirmations_patched
    )


def test_echo(
        patched_contract,
        use_tester: bool,
        monkeypatch: MonkeyPatch,
        sender_privkey: str,
        receiver_privkey: str,
        channel_manager_address: str,
        channel_manager: ChannelManager,
        web3: Web3,
        wait_for_blocks,
        revert_chain
):
    retry_interval = 5

    server = run_echo_server(
        receiver_privkey,
        channel_manager=channel_manager,
        join_thread=False
    )

    if use_tester:
        retry_interval = 0.1
        patch_session(web3, monkeypatch)
        wait_for_blocks(1)

    response = run_echo_client(
        sender_privkey,  # Hex-encoded private key works here too
        None,
        'echofix/hello',
        channel_manager_address=channel_manager_address,
        web3=web3,
        retry_interval=retry_interval
    )

    assert response.text == 'hello'

    response = run_echo_client(
        sender_privkey,  # Hex-encoded private key works here too
        None,
        'echodyn/13',
        channel_manager_address=channel_manager_address,
        web3=web3,
        retry_interval=retry_interval
    )

    assert response.text == '13'

    server.stop()
    server.join()

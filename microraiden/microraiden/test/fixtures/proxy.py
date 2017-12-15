import pytest

from microraiden.channel_manager import ChannelManager
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.proxy.resources import Expensive
import microraiden.proxy.resources.login as login
import logging
log = logging.getLogger(__name__)


class ExpensiveKitten(Expensive):
    def get(self, path):
        return "HI I AM A KITTEN"


class ExpensiveDoggo(Expensive):
    def get(self, path):
        return "HI I AM A DOGGO"


class ExpensiveTeapot(Expensive):
    def get(self, path):
        return "HI I AM A TEAPOT", 418


@pytest.fixture
def proxy_state_filename():
    return None


@pytest.fixture
def empty_proxy(channel_manager: ChannelManager, wait_for_blocks, use_tester: bool):
    app = PaywalledProxy(channel_manager)
    app.run()

    if use_tester:
        # Waiting only required on tester chains due to monkey-patched channel manager.
        wait_for_blocks(1)

    yield app
    app.stop()


@pytest.fixture
def doggo_proxy(
        channel_manager: ChannelManager,
        proxy_ssl: bool,
        proxy_ssl_certs
):
    app = PaywalledProxy(channel_manager)
    app.add_paywalled_resource(ExpensiveKitten, '/kitten.jpg', 1)
    app.add_paywalled_resource(ExpensiveDoggo, '/doggo.jpg', 2)
    app.add_paywalled_resource(ExpensiveTeapot, '/teapot.jpg', 3)
    ssl_context = proxy_ssl_certs if proxy_ssl else None
    app.run(ssl_context=ssl_context)
    yield app
    app.stop()


@pytest.fixture
def http_doggo_url(api_endpoint_address) -> str:
    return 'http://{}/doggo.jpg'.format(api_endpoint_address)


@pytest.fixture
def https_doggo_url(api_endpoint_address) -> str:
    return 'https://{}/doggo.jpg'.format(api_endpoint_address)


@pytest.fixture
def users_db():
    return login.userDB

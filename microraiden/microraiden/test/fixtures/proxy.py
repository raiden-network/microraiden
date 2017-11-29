import pytest

from microraiden.channel_manager import ChannelManager
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.proxy.content import (
    PaywalledContent,
)
import microraiden.proxy.resources.login as login


@pytest.fixture
def proxy_state_filename():
    return None


@pytest.fixture
def empty_proxy(channel_manager: ChannelManager, wait_for_blocks):
    app = PaywalledProxy(channel_manager)
    app.run()

    # Waiting only required on tester chains due to monkey patching.
    wait_for_blocks(1)

    yield app
    app.stop()


@pytest.fixture
def doggo_proxy(channel_manager, receiver_privkey, proxy_state_filename):
    app = PaywalledProxy(channel_manager)
    app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
    app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
    app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
#    app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
    app.run()
    yield app
    app.stop()


@pytest.fixture
def users_db():
    return login.userDB

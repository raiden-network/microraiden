import pytest
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy
from raiden_mps.proxy.content import (
    PaywalledFile,
    PaywalledContent,
    PaywalledProxyUrl
)


@pytest.fixture
def proxy_state_filename():
    return None


@pytest.fixture
def doggo_proxy(channel_manager, receiver_privkey, proxy_state_filename):
    app = PaywalledProxy(channel_manager)
    app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
    app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
    app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
    app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
    app.run(debug=True)
    yield app
    app.stop()

from gevent import monkey
monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blockchain").setLevel(logging.DEBUG)
logging.getLogger("channel_manager").setLevel(logging.DEBUG)

log = logging.getLogger(__name__)


from microraiden.make_helpers import make_paywalled_proxy
from microraiden.proxy.content import (
    PaywalledContent,
    PaywalledProxyUrl
)

from web3 import HTTPProvider, Web3
from flask import Flask
import config
import sys

#
# This is an example of a simple uwsgi/Flask app using Microraiden to pay for the content.
# Set up the configuration values in config.py (at least you must set PRIVATE_KEY, RPC_PROVIDER).
#

if config.PRIVATE_KEY is None:
    log.critical("config.py: PRIVATE_KEY is not set")
    sys.exit(1)

if config.RPC_PROVIDER is None:
    log.critical("config.py: RPC_PROVIDER is not set")
    sys.exit(1)

# create a custom web3 provider - parity/geth runs in another container/on another host
web3 = Web3(HTTPProvider(config.RPC_PROVIDER, request_kwargs={'timeout': 60}))

# create flask app
app = Flask(__name__)

# create microraiden app
microraiden_app = make_paywalled_proxy(config.PRIVATE_KEY, config.STATE_FILE,
                                       web3=web3, flask_app=app)
# add some content
microraiden_app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
microraiden_app.add_content(PaywalledProxyUrl(".*", 1, "http://en.wikipedia.org/", [r"wiki/.*"]))

# only after blockchain is fully synced the app is ready to serve requests
microraiden_app.channel_manager.wait_sync()

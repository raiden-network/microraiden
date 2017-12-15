from gevent import monkey
monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blockchain").setLevel(logging.DEBUG)
logging.getLogger("channel_manager").setLevel(logging.DEBUG)

log = logging.getLogger(__name__)


from microraiden.make_helpers import make_paywalled_proxy
from requests.exceptions import ConnectionError

from web3 import HTTPProvider, Web3
from flask import Flask
import config
import sys
import uwsgi
import gevent
from bs4 import BeautifulSoup
from flask import make_response
import io
from microraiden.proxy.content import PaywalledProxyUrl
from microraiden.config import JSLIB_DIR, JSPREFIX_URL, TKN_DECIMALS


#
# This is an example of a simple uwsgi/Flask app using Microraiden to pay for the content.
# Set up the configuration values in config.py (at least you must set PRIVATE_KEY, WEB3_PROVIDER).
#

if config.PRIVATE_KEY is None:
    log.critical("config.py: PRIVATE_KEY is not set")
    sys.exit(1)

if config.WEB3_PROVIDER is None:
    log.critical("config.py: WEB3_PROVIDER is not set")
    sys.exit(1)

# create a custom web3 provider - parity/geth runs in another container/on another host

while True:
    try:
        web3 = Web3(HTTPProvider(config.WEB3_PROVIDER, request_kwargs={'timeout': 60}))
        network_id = web3.version.network
    except ConnectionError:
        log.critical("Ethereum node isn't responding. Restarting after %d seconds."
                     % (config.SLEEP_RELOAD))
        gevent.sleep(config.SLEEP_RELOAD)
    else:
        break

# create flask app
app = Flask(__name__, static_url_path=JSPREFIX_URL, static_folder=JSLIB_DIR)

# create microraiden app
microraiden_app = make_paywalled_proxy(config.PRIVATE_KEY,
                                       config.STATE_FILE,
                                       web3=web3,
                                       flask_app=app)
# add some content
microraiden_app.add_content(PaywalledProxyUrl(".*",
                                              1 * TKN_DECIMALS,
                                              "http://en.wikipedia.org/",
                                              [r"wiki/.*"]))

# only after blockchain is fully synced the app is ready to serve requests
microraiden_app.channel_manager.wait_sync()

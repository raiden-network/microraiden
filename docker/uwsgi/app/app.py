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
from microraiden.examples.demo_proxy.fortunes import PaywalledFortune

class MyPaywalledFortune(PaywalledFortune):
    def __init__(self, path, cost, filepath):
        super(MyPaywalledFortune, self).__init__(path, cost, filepath)
        html_tmpl = io.open('web/fortunes_tmpl.html', 'r', encoding='utf8').read()
        self.soup_tmpl = BeautifulSoup(html_tmpl, 'html.parser')

    def get(self, url):
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        text = self.fortunes.get()
        return make_response(self.generate_html(text), 200, headers)

    def generate_html(self, text):
        div = self.soup_tmpl.find('div', {"id" : "fortunes-text"})
        div.h1.string = text
        return str(self.soup_tmpl)




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

try:
    web3 = Web3(HTTPProvider(config.RPC_PROVIDER, request_kwargs={'timeout': 60}))
    network_id = web3.version.network
except ConnectionError:
    log.critical("Ethereum node isn't responding. Restarting after %d seconds."
                 % (config.SLEEP_RELOAD))
    gevent.sleep(config.SLEEP_RELOAD)
    uwsgi.reload()

# create flask app
app = Flask(__name__)

# create microraiden app
microraiden_app = make_paywalled_proxy(config.PRIVATE_KEY, config.STATE_FILE,
                                       web3=web3, flask_app=app)
# add some content
microraiden_app.add_content(MyPaywalledFortune("fortunes_en", 1, "microraiden/data/fortunes"))
microraiden_app.add_content(MyPaywalledFortune("fortunes_cn", 1, "microraiden/data/chinese"))

# only after blockchain is fully synced the app is ready to serve requests
microraiden_app.channel_manager.wait_sync()

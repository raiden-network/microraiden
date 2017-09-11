from gevent import monkey
monkey.patch_all()

import logging
#logging.basicConfig(filename="/app/mr.log",level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blockchain").setLevel(logging.DEBUG)
logging.getLogger("channel_manager").setLevel(logging.DEBUG)

from microraiden.make_helpers import make_paywalled_proxy
from microraiden import config
from flask import Flask
from microraiden.crypto import privkey_to_addr
import os
from microraiden.proxy.content import (
    PaywalledFile,
    PaywalledContent
)

from web3 import HTTPProvider, Web3
flask_app = Flask(__name__)

private_key ='b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
receiver_address = privkey_to_addr(private_key)
channel_manager_address = config.CHANNEL_MANAGER_ADDRESS
rpc_provider = 'http://172.18.0.1:8545'
host='localhost'
port='8080'

state_file = "%s_%s.pkl" % (channel_manager_address[:10], receiver_address[:10])
state_file = None

config.paywall_html_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../webui'))
web3 = Web3(HTTPProvider(rpc_provider, request_kwargs={'timeout': 60}))
app = make_paywalled_proxy(private_key, state_file, web3=web3, flask_app=flask_app)
app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
#app.add_content(PaywalledContent("doggo.txt", 2, get_doggo))
app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
app.channel_manager.wait_sync()
#app.run(host=host, port=port, debug=True, ssl_context=(ssl_key, ssl_cert))
#app.join()



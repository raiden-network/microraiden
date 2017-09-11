from gevent import monkey
monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blockchain").setLevel(logging.DEBUG)
logging.getLogger("channel_manager").setLevel(logging.DEBUG)

log = logging.getLogger(__name__)

from microraiden.make_helpers import make_paywalled_proxy
from microraiden import config
from flask import Flask, safe_join
from microraiden.crypto import privkey_to_addr
import os
import mimetypes
import werkzeug
from microraiden.proxy.content import (
    PaywalledFile,
    PaywalledContent
)

# Function similar to send_from_directory, but setting X-Accel-Redirect instead
# To use it, xsendfile_path needs to be configured in nginx, like:
## xsendfile_path = "/dist/" ; nginx.conf:
#location /dist/ {
#    internal;
#    root /app/ng ;
#}
def send_xaccel_dir(directory, filename, xsendfile_path, **opts):
    path = safe_join(directory, filename)
    if not os.path.isfile(path):
        abort(404)

    MT = mimetypes.guess_type(filename, strict=False)[0] or \
            "application/octet-stream"
    H = werkzeug.datastructures.Headers()
    log.debug(safe_join(xsendfile_path, filename))
    H["X-Accel-Redirect"] = safe_join(xsendfile_path, filename)
    log.debug(xsendfile_path + " " + filename)

    return app.response_class(None, mimetype=MT, headers=H, **opts)

from web3 import HTTPProvider, Web3
app = Flask(__name__)

@app.route("/xtest")
def favicon():
    return send_xaccel_dir("/files/", "test.txt",
            "/fileso/", status=200)

private_key ='b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
receiver_address = privkey_to_addr(private_key)
channel_manager_address = config.CHANNEL_MANAGER_ADDRESS
rpc_provider = 'http://172.18.0.1:8545'
host='localhost'
port='8080'

state_file = "/files/%s_%s.pkl" % (channel_manager_address[:10], receiver_address[:10])

# create microraiden targets
config.paywall_html_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../webui'))
web3 = Web3(HTTPProvider(rpc_provider, request_kwargs={'timeout': 60}))

microraiden_app = make_paywalled_proxy(private_key, state_file, web3=web3, flask_app=app)
microraiden_app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
microraiden_app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
microraiden_app.channel_manager.wait_sync()
#app.run(host=host, port=port, debug=True, ssl_context=(ssl_key, ssl_cert))
#app.join()



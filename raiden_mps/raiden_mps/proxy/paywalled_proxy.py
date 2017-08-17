import gevent
import sys
from gevent import monkey
monkey.patch_all()
from flask import Flask
from flask_restful import (
    Api,
)

from raiden_mps.channel_manager import (
    ChannelManager,
    StateReceiverAddrMismatch,
    StateContractAddrMismatch
)

from raiden_mps.proxy.resources import (
    Expensive,
    ChannelManagementAdmin,
    ChannelManagementListChannels,
    ChannelManagementChannelInfo,
    ChannelManagementRoot,
    StaticFilesServer
)

from raiden_mps.proxy.content import PaywallDatabase
from raiden_mps.proxy.resources.expensive import LightClientProxy

from web3 import Web3
from web3.providers.rpc import RPCProvider
from ethereum.utils import encode_hex, privtoaddr

import raiden_mps.utils as utils
import logging

log = logging.getLogger(__name__)


JSLIB_DIR = 'raiden_mps/data/html/'
INDEX_HTML = JSLIB_DIR + 'index.html'


class PaywalledProxy:
    def __init__(self, contract_address,
                 private_key, state_filename,
                 flask_app=None):
        if not flask_app:
            self.app = Flask(__name__)
        else:
            assert isinstance(flask_app, Flask)
            self.app = flask_app
        self.paywall_db = PaywallDatabase()
        self.api = Api(self.app)
        self.rest_server = None
        self.server_greenlet = None
        web3 = Web3(RPCProvider())
        receiver_address = '0x' + encode_hex(privtoaddr(private_key)).decode()

        try:
            self.channel_manager = ChannelManager(
                web3,
                utils.get_contract_proxy(web3, private_key, contract_address),
                receiver_address,
                private_key,
                state_filename=state_filename,
                channel_contract_address=contract_address
            )
        except StateReceiverAddrMismatch as e:
            log.error('Receiver address does not match address stored in a saved state. '
                      'Use a different file, or backup and remove %s. (%s)' %
                      (state_filename, e))
            sys.exit(1)

        except StateContractAddrMismatch as e:
            self.log.error('channel contract address mismatch. '
                           'Saved state file is %s. Backup it, remove, then'
                           'start proxy again (%s)' %
                           (state_filename, e))
            sys.exit(1)
        self.channel_manager.start()

        cfg = {
            'contract_address': contract_address,
            'receiver_address': receiver_address,
            'channel_manager': self.channel_manager,
            'paywall_db': self.paywall_db,
            'light_client_proxy': LightClientProxy(INDEX_HTML)
        }
        self.api.add_resource(StaticFilesServer, "/js/<path:content>",
                              resource_class_kwargs={'directory': JSLIB_DIR})
        self.api.add_resource(Expensive, "/<path:content>", resource_class_kwargs=cfg)
        self.api.add_resource(ChannelManagementChannelInfo,
                              "/cm/channels/<string:sender_address>/<int:opening_block>",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementAdmin, "/cm/admin",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementListChannels, "/cm/channels/",
                              "/cm/channels/<string:sender_address>",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementRoot, "/cm")

    def add_content(self, content):
        self.paywall_db.add_content(content)

    def run(self, debug=False):
        self.channel_manager.wait_sync()
        from gevent.wsgi import WSGIServer
        self.rest_server = WSGIServer(('localhost', 5000), self.app)
        self.server_greenlet = gevent.spawn(self.rest_server.serve_forever)

    def stop(self):
        assert self.rest_server is not None
        assert self.server_greenlet is not None
        # we should stop the server only if it has been started. In case we do stop()
        #  right after start(), the server may be in an undefined state and join() will
        #  hang indefinetely (this often happens with tests)
        for try_n in range(5):
            if self.rest_server.started is True:
                break
            gevent.sleep(1)
        self.rest_server.stop()
        self.server_greenlet.join()

    def join(self):
        self.server_greenlet.join()

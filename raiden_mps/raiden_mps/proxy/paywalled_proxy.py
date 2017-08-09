from flask import Flask
from flask_restful import (
    Api,
)

from raiden_mps.channel_manager import (
    ChannelManager,
    Blockchain,
)

from raiden_mps.proxy.resources import (
    Expensive,
    ChannelManagementAdmin,
    ChannelManagementClose,
    ChannelManagementRoot
)

from raiden_mps.test.utils import BlockchainMock
from raiden_mps.proxy.content import PaywallDatabase

from web3 import Web3
from web3.providers.rpc import RPCProvider


class PaywalledProxy:
    def __init__(self, blockchain, config, flask_app=None):
        assert isinstance(blockchain, Blockchain) or isinstance(blockchain, BlockchainMock)
        if not flask_app:
            self.app = Flask(__name__)
        else:
            assert isinstance(flask_app, Flask)
            self.app = flask_app
        self.paywall_db = PaywallDatabase()
        self.config = config
        self.api = Api(self.app)
        self.channel_manager = ChannelManager(
            Web3(RPCProvider()),
            None,
            config['receiver_address'],
            config['private_key']
        )

        cfg = {
            'contract_address': self.config['contract_address'],
            'receiver_address': self.config['receiver_address'],
            'channel_manager': self.channel_manager,
            'paywall_db': self.paywall_db
        }
        self.api.add_resource(Expensive, "/<path:content>", resource_class_kwargs=cfg)

        self.api.add_resource(ChannelManagementAdmin, "/cm/admin")
        self.api.add_resource(ChannelManagementClose, "/cm/close")
        self.api.add_resource(ChannelManagementRoot, "/cm")

    def add_content(self, content):
        self.paywall_db.add_content(content)

    def run(self, debug=False):
        self.app.run(debug=debug)

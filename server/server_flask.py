from flask import Flask
from flask_restful import (
    Api,
)

from server import (
    ChannelManager,
    ChannelManagerState,
    Blockchain,
)

from resources import (
    Expensive,
    ChannelManagementAdmin,
    ChannelManagementClose,
    ChannelManagementRoot
)


class PaymentProxy:
    config = {
        "contract_address": "0x" + "1" * 40,
        "receiver_address": "0x" + "2" * 40,
    }

    def __init__(self, blockchain):
        assert isinstance(blockchain, Blockchain)
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.channel_manager = ChannelManager(
            self.config['receiver_address'], blockchain,
            lambda *args: ChannelManagerState(self.config['contract_address'],
                                              self.config['receiver_address']))
        self.api.add_resource(Expensive, '/expensive/<path:content>',
                              resource_class_kwargs={
                                  'price': 1,
                                  'contract_address': self.config['contract_address'],
                                  'receiver_address': self.config['receiver_address'],
                                  'channel_manager': self.channel_manager})

        self.api.add_resource(ChannelManagementAdmin, "/cm/admin")
        self.api.add_resource(ChannelManagementClose, "/cm/close")
        self.api.add_resource(ChannelManagementRoot, "/cm")

    def run(self, debug=False):
        self.app.run(debug=debug)


if __name__ == '__main__':
    blockchain = Blockchain(None)
    app = PaymentProxy(blockchain)
    app.run(debug=True)

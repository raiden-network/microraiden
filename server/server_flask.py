from flask import Flask
from flask import request
from flask_restful import (
    Api,
    Resource
)

from server import (
    ChannelManager,
    ChannelManagerState,
    Blockchain
)


class RequestData:
    PRICE = 'RDN-Price'
    CONTRACT_ADDRESS = 'RDN-Contract-Address'
    RECEIVER_ADDRESS = 'RDN-Receiver-Address'
    PAYMENT = 'RDN-Payment'
    BALANCE = 'RDN-Balance'
    BALANCE_SIGNATURE = 'RDN-Balance-Signature'

    def __init__(self, headers):
        """parse a flask request object and check if the data received are valid"""
        from werkzeug import EnvironHeaders
        assert isinstance(headers, EnvironHeaders)
        self.check_headers(headers)

    @staticmethod
    def get_response(price, contract_addr, receiver_addr):
        return {
            RequestData.PRICE: price,
            RequestData.CONTRACT_ADDRESS: contract_addr,
            RequestData.RECEIVER_ADDRESS: receiver_addr
        }

    def check_headers(self, headers):
        """Check if headers sent by the client are valid"""
        price = headers.get(RequestData.PRICE, None)
        contract_address = headers.get(RequestData.CONTRACT_ADDRESS, None)
        receiver_address = headers.get(RequestData.RECEIVER_ADDRESS, None)
        payment = headers.get(RequestData.PAYMENT, None)
        balance_signature = headers.get(RequestData.BALANCE_SIGNATURE, None)
        price = int(price)
        if price and price < 0:
            raise ValueError("Price must be >= 0")
        if contract_address and not is_valid_address(contract_address):
            raise ValueError("Invalid contract address")
        if receiver_address and not is_valid_address(receiver_address):
            raise ValueError("Invalid receiver address")
        if payment and not isinstance(payment, int):
            raise ValueError("Payment must be an integer")

        self.price = price
        self.contract_address = contract_address
        self.receiver_address = receiver_address
        self.payment = payment
        self.balance_signature = balance_signature


def is_valid_address(address):
    return address


class Expensive(Resource):
    def __init__(self, price, contract_address, receiver_address, channel_manager):
        super(Expensive, self).__init__()
        assert isinstance(channel_manager, ChannelManager)
        assert is_valid_address(contract_address)
        assert is_valid_address(receiver_address)
        self.price = price
        self.contract_address = is_valid_address(contract_address)
        self.receiver_address = is_valid_address(receiver_address)
        self.channel_manager = channel_manager

    def get(self, content):
        try:
            data = RequestData(request.headers)
        except ValueError as e:
            return 409, str(e)

        # mock
        if data.balance_signature:
            return self.reply_premium()
        else:
            return self.reply_payment_required()
        # /mock
        if self.channel_manager.register_payment(data.balance_signature):
            return self.reply_premium()
        else:
            return self.reply_payment_required()

    def reply_premium(self):
        return "PREMIUM CONTENT", 200

    def reply_payment_required(self):
        return "Payment required", 402, RequestData.get_response(
            self.price,
            self.contract_address,
            self.receiver_address)


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

    def run(self, debug=False):
        self.app.run(debug=debug)


if __name__ == '__main__':
    blockchain = Blockchain(None)
    app = PaymentProxy(blockchain)
    app.run(debug=True)

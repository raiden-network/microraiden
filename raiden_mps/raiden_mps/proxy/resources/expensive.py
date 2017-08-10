from flask import request
from flask_restful import (
    Resource
)
from raiden_mps.channel_manager import (
    ChannelManager,
)
# from raiden_mps.utils import parse_balance_proof_msg

from raiden_mps.header import HTTPHeaders as header
from raiden_mps.config import CM_API_ROOT

from flask import Response


class RequestData:
    def __init__(self, headers):
        """parse a flask request object and check if the data received are valid"""
        from werkzeug.datastructures import EnvironHeaders
        assert isinstance(headers, EnvironHeaders)
        self.check_headers(headers)
#        self.sender_address, _ = parse_balance_proof_msg(self.balance_signature, 2, 3, 4)
        self.sender_address = 0

    def check_headers(self, headers):
        """Check if headers sent by the client are valid"""
        price = headers.get(header.PRICE, None)
        contract_address = headers.get(header.CONTRACT_ADDRESS, None)
        receiver_address = headers.get(header.RECEIVER_ADDRESS, None)
        payment = headers.get(header.PAYMENT, None)
        balance_signature = headers.get(header.BALANCE_SIGNATURE, None)
        if price:
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
    def __init__(self, contract_address, receiver_address, channel_manager, paywall_db):
        super(Expensive, self).__init__()
        assert isinstance(channel_manager, ChannelManager)
        assert is_valid_address(contract_address)
        assert is_valid_address(receiver_address)
        self.contract_address = is_valid_address(contract_address)
        self.receiver_address = is_valid_address(receiver_address)
        self.channel_manager = channel_manager
        self.paywall_db = paywall_db

    def get(self, content):
        try:
            data = RequestData(request.headers)
        except ValueError as e:
            return str(e), 409
        proxy_handle = self.paywall_db.get_content(content)
        if proxy_handle is None:
            return "NOT FOUND", 404
        if data.balance_signature:
            # check the balance proof
            return self.reply_premium(content, data.sender_address, proxy_handle)
        else:
            return self.reply_payment_required(content, proxy_handle)

    def reply_premium(self, content, sender_address, proxy_handle, sender_balance=0):
        headers = {
            header.GATEWAY_PATH: CM_API_ROOT,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.SENDER_ADDRESS: sender_address,
            header.SENDER_BALANCE: sender_balance
        }
        response = proxy_handle.get(content)
        if isinstance(response, Response):
            return response
        else:
            data, status_code = response
            return data, status_code, headers

    def reply_payment_required(self, content, proxy_handle):
        headers = {
            header.GATEWAY_PATH: CM_API_ROOT,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.PRICE: proxy_handle.price,
        }
        return "Payment required", 402, headers

from flask import request
from flask_restful import (
    Resource
)
from raiden_mps.channel_manager import (
    ChannelManager,
    NoOpenChannel,
    InvalidBalanceProof
)
# from raiden_mps.utils import parse_balance_proof_msg

from raiden_mps.header import HTTPHeaders as header
from raiden_mps.config import CM_API_ROOT

from flask import Response, make_response

import raiden_mps.config as config


class RequestData:
    def __init__(self, headers, cookies=None):
        """parse a flask request object and check if the data received are valid"""
        from werkzeug.datastructures import EnvironHeaders
        assert isinstance(headers, EnvironHeaders)
        self.check_headers(headers)
        if cookies:
            self.check_cookies(cookies)
#        self.sender_address, _ = parse_balance_proof_msg(self.balance_signature, 2, 3, 4)
        self.sender_address = 0

    def check_cookies(self, cookies):
        if header.BALANCE_SIGNATURE in cookies:
            self.balance_signature = cookies.get(header.BALANCE_SIGNATURE)
        if header.OPEN_BLOCK in cookies:
            self.open_block_number = int(cookies.get(header.OPEN_BLOCK))
        if header.SENDER_BALANCE in cookies:
            self.balance = int(cookies.get(header.SENDER_BALANCE))

    def check_headers(self, headers):
        """Check if headers sent by the client are valid"""
        price = headers.get(header.PRICE, None)
        contract_address = headers.get(header.CONTRACT_ADDRESS, None)
        receiver_address = headers.get(header.RECEIVER_ADDRESS, None)
        sender_address = headers.get(header.SENDER_ADDRESS, None)
        payment = headers.get(header.PAYMENT, None)
        balance_signature = headers.get(header.BALANCE_SIGNATURE, None)
        open_block = headers.get(header.OPEN_BLOCK, None)
        balance = headers.get(header.SENDER_BALANCE, None)
        if price:
            price = int(price)
        if open_block:
            open_block = int(open_block)
        if balance:
            balance = int(balance)
        if price and price < 0:
            raise ValueError("Price must be >= 0")
        if contract_address and not is_valid_address(contract_address):
            raise ValueError("Invalid contract address")
        if receiver_address and not is_valid_address(receiver_address):
            raise ValueError("Invalid receiver address")
        if sender_address and not is_valid_address(sender_address):
            raise ValueError("Invalid sender address")
        if payment and not isinstance(payment, int):
            raise ValueError("Payment must be an integer")
        if open_block and open_block < 0:
            raise ValueError("Open block must be >= 0")
        if balance and balance < 0:
            raise ValueError("Balance must be >= 0")

        self.price = price
        self.contract_address = contract_address
        self.receiver_address = receiver_address
        self.payment = payment
        self.balance_signature = balance_signature
        self.sender_address = sender_address
        self.open_block_number = open_block
        self.balance = balance


class LightClientProxy:
    def __init__(self, index_html):
        self.data = open(index_html).read()

    def get(self, receiver, amount, token):
#        js_params = '''window.RMPparams = {
#            receiver: "%s"
#            amount: %d,
#            token: "%s",
#        };''' % (receiver, amount, token)
#        soup = bs4.BeautifulSoup(self.data, "html.parser")
#        js_tag = soup.new_tag('script', type="text/javascript")
#        js_tag.string = js_params
#        soup.body.insert(0, js_tag)
        return self.data


def is_valid_address(address):
    return address


class Expensive(Resource):
    def __init__(self, contract_address, receiver_address,
                 channel_manager, paywall_db,
                 light_client_proxy=None
                 ):
        super(Expensive, self).__init__()
        assert isinstance(channel_manager, ChannelManager)
        assert is_valid_address(contract_address)
        assert is_valid_address(receiver_address)
        self.contract_address = is_valid_address(contract_address)
        self.receiver_address = is_valid_address(receiver_address)
        self.channel_manager = channel_manager
        self.paywall_db = paywall_db
        self.light_client_proxy = light_client_proxy

    def get(self, content):
        try:
            data = RequestData(request.headers, request.cookies)
        except ValueError as e:
            return str(e), 409
        proxy_handle = self.paywall_db.get_content(content)
        if proxy_handle is None:
            return "NOT FOUND", 404
        if data.balance_signature:
            # check the balance proof
            try:
                self.channel_manager.register_payment(
                    self.receiver_address,
                    data.open_block_number,
                    data.balance,
                    data.balance_signature)
            except NoOpenChannel as e:
                return str(e), 402, {header.INSUF_CONFS: "1"}
            except InvalidBalanceProof as e:
                return str(e), 402, {header.INSUF_FUNDS: "1"}
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
        if callable(proxy_handle.price):
            price = proxy_handle.price(content)
        elif isinstance(proxy_handle.price, int):
            price = proxy_handle.price
        else:
            return "Invalid price attribute", 500
        headers = {
            "Content-Type": "text/html",
            header.GATEWAY_PATH: CM_API_ROOT,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.PRICE: price
        }

        if self.light_client_proxy:
            data = self.light_client_proxy.get(self.receiver_address, price, config.TOKEN_ADDRESS)
        else:
            data = ""
        reply = make_response(data, 402, headers)
        for hdr in (header.GATEWAY_PATH, header.CONTRACT_ADDRESS,
                    header.RECEIVER_ADDRESS, header.PRICE):
            reply.set_cookie(hdr, str(headers[hdr]))
        return reply

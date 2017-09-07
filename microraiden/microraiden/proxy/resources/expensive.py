import logging
from flask_restful import (
    Resource
)
from microraiden.channel_manager import (
    ChannelManager,
    Channel,
    NoOpenChannel,
    InvalidBalanceProof,
    InvalidBalanceAmount,
    InsufficientConfirmations
)
from microraiden.proxy.content import PaywalledContent
# from microraiden.utils import parse_balance_proof_msg

from microraiden import HTTPHeaders as header
import microraiden.config as config

from flask import Response, make_response, request

log = logging.getLogger(__name__)


class RequestData:
    def __init__(self, headers, cookies=None):
        """parse a flask request object and check if the data received are valid"""
        from werkzeug.datastructures import EnvironHeaders
        assert isinstance(headers, EnvironHeaders)
        self.check_headers(headers)
        if cookies:
            self.check_cookies(cookies)

    def check_cookies(self, cookies):
        if header.BALANCE_SIGNATURE in cookies:
            self.balance_signature = cookies.get(header.BALANCE_SIGNATURE)
        if header.OPEN_BLOCK in cookies:
            self.open_block_number = int(cookies.get(header.OPEN_BLOCK))
        if header.SENDER_BALANCE in cookies:
            self.balance = int(cookies.get(header.SENDER_BALANCE))
        if header.SENDER_ADDRESS in cookies:
            self.sender_address = cookies.get(header.SENDER_ADDRESS)

    def check_headers(self, headers):
        """Check if headers sent by the client are valid"""
        price = headers.get(header.PRICE, None)
        contract_address = headers.get(header.CONTRACT_ADDRESS, None)
        receiver_address = headers.get(header.RECEIVER_ADDRESS, None)
        sender_address = headers.get(header.SENDER_ADDRESS, None)
        payment = headers.get(header.PAYMENT, None)
        balance_signature = headers.get(header.BALANCE_SIGNATURE, None)
        open_block = headers.get(header.OPEN_BLOCK, None)
        balance = headers.get(header.BALANCE, None)
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

    def get(self, content, receiver, amount, token):
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
        log.info(content)
        if self.channel_manager.node_online() is False:
            return "Ethereum node is not responding", 502
        try:
            data = RequestData(request.headers, request.cookies)
        except ValueError as e:
            return str(e), 409
        proxy_handle = self.paywall_db.get_content(content)
        if proxy_handle is None:
            return "NOT FOUND", 404

        if proxy_handle.is_paywalled(content) is False:
            return self.reply_premium(content, proxy_handle, {})

        accepts_html = r'text/html' in request.headers.get('Accept', '')

        if not data.balance_signature:
            return self.reply_payment_required(content, proxy_handle, gen_ui=accepts_html)

        # try to get an existing channel
        try:
            channel = self.channel_manager.verify_balance_proof(
                data.sender_address, data.open_block_number,
                data.balance, data.balance_signature)
        except InsufficientConfirmations as e:
            headers = {header.INSUF_CONFS: "1"}
            return self.reply_payment_required(
                content, proxy_handle, headers=headers, gen_ui=accepts_html)
        except NoOpenChannel as e:
            return self.reply_payment_required(content, proxy_handle,
                                               headers={header.NONEXISTING_CHANNEL: 1},
                                               gen_ui=accepts_html)
        except InvalidBalanceAmount as e:
            # balance sent to the proxy is less than in the previous proof
            return self.reply_payment_required(content, proxy_handle, headers, gen_ui=accepts_html)
        except InvalidBalanceProof as e:
            return self.reply_payment_required(content, proxy_handle,
                                               headers={header.INVALID_PROOF: 1},
                                               gen_ui=accepts_html)

        # set the headers to reflect actual state of a channel
        headers = self.generate_headers(channel, proxy_handle)
        try:
            self.channel_manager.register_payment(
                channel.sender,
                data.open_block_number,
                data.balance,
                data.balance_signature)
        except InvalidBalanceAmount as e:
            # balance sent to the proxy is less than in the previous proof
            return self.reply_payment_required(content, proxy_handle, headers, gen_ui=accepts_html)
        except InvalidBalanceProof as e:
            return self.reply_payment_required(content, proxy_handle, headers, gen_ui=accepts_html)

        # all ok, return premium content
        return self.reply_premium(content, proxy_handle, headers)

    def generate_headers(self, channel: Channel, proxy_handle: PaywalledContent):
        assert channel.sender is not None
        assert channel.balance >= 0
        headers = {
            header.GATEWAY_PATH: config.API_PATH,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.PRICE: proxy_handle.price,
            header.SENDER_ADDRESS: channel.sender,
            header.SENDER_BALANCE: channel.balance,
        }
        if channel.last_signature is not None:
            headers.update({header.BALANCE_SIGNATURE: channel.last_signature})
        return headers

        return headers

    def reply_premium(self, content, proxy_handle, headers):
        response = proxy_handle.get(content)
        if isinstance(response, Response):
            return response
        else:
            data, status_code = response
            return data, status_code, headers

    def reply_payment_required(self, content, proxy_handle, headers=None, gen_ui=False):
        if headers is None:
            headers = {}
        assert isinstance(headers, dict)
        assert isinstance(gen_ui, bool)
        if callable(proxy_handle.price):
            price = proxy_handle.price(content)
        elif isinstance(proxy_handle.price, int):
            price = proxy_handle.price
        else:
            return "Invalid price attribute", 500
        headers.update({
            header.GATEWAY_PATH: config.API_PATH,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.PRICE: price,
            header.TOKEN_ADDRESS: config.TOKEN_ADDRESS
        })
        if gen_ui is True:
            return self.get_webUI_reply(content, proxy_handle, price, headers)
        else:
            return make_response('', 402, headers)

    def get_webUI_reply(self, content: str, proxy_handle: PaywalledContent,
                        price: int, headers: dict):
        headers.update({
            "Content-Type": "text/html",
        })
        data = proxy_handle.get_paywall(content, self.receiver_address,
                                        price, config.TOKEN_ADDRESS)
        reply = make_response(data, 402, headers)
        for hdr in (header.GATEWAY_PATH,
                    header.CONTRACT_ADDRESS,
                    header.RECEIVER_ADDRESS,
                    header.PRICE,
                    header.NONEXISTING_CHANNEL,
                    header.TOKEN_ADDRESS):
            if hdr in headers:
                reply.set_cookie(hdr, str(headers[hdr]))
        return reply

import logging
from flask import Response, make_response, request
from microraiden import HTTPHeaders as header
from flask_restful.utils import unpack

from microraiden.channel_manager import (
    ChannelManager,
)
from microraiden.exceptions import (
    NoOpenChannel,
    InvalidBalanceProof,
    InvalidBalanceAmount,
    InsufficientConfirmations
)
import microraiden.constants as constants
from microraiden.proxy.resources.request_data import RequestData
from functools import wraps
from eth_utils import is_address

log = logging.getLogger(__name__)


class Paywall(object):
    def __init__(self,
                 channel_manager,
                 light_client_proxy=None
                 ):
        super().__init__()
        assert isinstance(channel_manager, ChannelManager)
        assert is_address(channel_manager.channel_manager_contract.address)
        assert is_address(channel_manager.receiver)
        self.contract_address = channel_manager.channel_manager_contract.address
        self.receiver_address = channel_manager.receiver
        self.channel_manager = channel_manager
        self.light_client_proxy = light_client_proxy

    def access(self, resource, method, *args, **kwargs):
        if self.channel_manager.node_online() is False:
            return "Ethereum node is not responding", 502
        if self.channel_manager.get_eth_balance() < constants.PROXY_BALANCE_LIMIT:
            return "Channel manager ETH balance is below limit", 502
        try:
            data = RequestData(request.headers, request.cookies)
        except ValueError as e:
            return str(e), 409
        accepts_html = (
            'text/html' in request.accept_mimetypes and
            request.accept_mimetypes.best != '*/*'
        )
        headers = {}

        price = resource.price()

        # payment required
        if price > 0:
            paywall, headers = self.paywall_check(price, data)
            if paywall and accepts_html is True:
                reply_data = resource.get_paywall(request.path)
                return self.reply_webui(reply_data, headers)
            elif paywall:
                return make_response('', 402, headers)

        # all ok, return actual content
        resp = method(request.path, *args, **kwargs)

        # merge headers, resource headers take precedence
        headers_lower = {key.lower(): value for key, value in headers.items()}
        lower_to_case = {key.lower(): key for key in headers}

        if isinstance(resp, Response):
            resource_headers = (key for key, value in resp.headers)
        else:
            data, code, resource_headers = unpack(resp)

        for key in resource_headers:
            key_lower = key.lower()
            if key_lower in headers_lower:
                headers.pop(lower_to_case[key_lower])

        if isinstance(resp, Response):
            resp.headers.extend(headers)
            return resp
        else:
            headers.update(resource_headers)
            return make_response(str(data), code, resource_headers)

    def paywall_check(self, price, data):
        """Check if the resource can be sent to the client.
        Returns (is_paywalled: Bool, http_headers: dict)
        """
        headers = self.generate_headers(price)
        if not data.balance_signature:
            return True, headers

        # try to get an existing channel
        try:
            channel = self.channel_manager.verify_balance_proof(
                data.sender_address, data.open_block_number,
                data.balance, data.balance_signature)
        except InsufficientConfirmations as e:
            log.debug('Refused payment: Insufficient confirmations (sender=%s, block=%d)' %
                      (data.sender_address, data.open_block_number))
            headers.update({header.INSUF_CONFS: "1"})
            return True, headers
        except NoOpenChannel as e:
            log.debug('Refused payment: Channel does not exist (sender=%s, block=%d)' %
                      (data.sender_address, data.open_block_number))
            headers.update({header.NONEXISTING_CHANNEL: "1"})
            return True, headers
        except InvalidBalanceAmount as e:
            log.debug('Refused payment: Invalid balance amount: %s (sender=%s, block=%d)' %
                      (str(e), data.sender_address, data.open_block_number))
            headers.update({header.INVALID_PROOF: 1})
            return True, headers
        except InvalidBalanceProof as e:
            log.debug('Refused payment: Invalid balance proof: %s (sender=%s, block=%d)' %
                      (str(e), data.sender_address, data.open_block_number))
            headers.update({header.INVALID_PROOF: 1})
            return True, headers

        # set headers to reflect channel state
        assert channel.sender is not None
        assert channel.balance >= 0
        headers.update(
            {
                header.SENDER_ADDRESS: channel.sender,
                header.SENDER_BALANCE: channel.balance
            })
        if channel.last_signature is not None:
            headers.update({header.BALANCE_SIGNATURE: channel.last_signature})

        amount_sent = data.balance - channel.balance

        if amount_sent != 0 and amount_sent != price:
            headers[header.INVALID_AMOUNT] = 1
            #  if difference is 0, it will be handled by channel manager
            return True, headers

        # set the headers to reflect actual state of a channel
        try:
            self.channel_manager.register_payment(
                channel.sender,
                data.open_block_number,
                data.balance,
                data.balance_signature)
        except (InvalidBalanceAmount, InvalidBalanceProof):
            # balance sent to the proxy is less than in the previous proof
            return True, headers

        # all ok, return premium content
        return False, headers

    # when are these generated?
    def generate_headers(self, price: int):
        assert price > 0
        """Generate basic headers that are sent back for every request"""
        headers = {
            header.GATEWAY_PATH: constants.API_PATH,
            header.RECEIVER_ADDRESS: self.receiver_address,
            header.CONTRACT_ADDRESS: self.contract_address,
            header.TOKEN_ADDRESS: self.channel_manager.get_token_address(),
            header.PRICE: price,
            'Content-Type': 'application/json'
        }
        return headers

    def reply_webui(self, reply_data='', headers: dict={}):
        headers.update({
            "Content-Type": "text/html",
        })
        reply = make_response(reply_data, 402, headers)
        for k, v in headers.items():
            if k.startswith('RDN-'):
                reply.set_cookie(k, str(v))
        return reply


def paywall_decorator(func):
    """Method decorator for Flask's Resource object. It magically makes
    every method paywalled.
    Example:
        class MyPaywalledResource(Resource):
            method_decorators = [paywall_decorator]
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = func.__self__  # get instance of the bound method
        return self.paywall.access(
            self,
            func,
            *args,
            **kwargs
        )
    return wrapper

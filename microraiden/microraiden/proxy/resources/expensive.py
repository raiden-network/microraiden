import logging

from microraiden.channel_manager import (
    ChannelManager,
)

from flask_restful import Resource
from eth_utils import is_address
from .paywall_decorator import paywall_decorator

log = logging.getLogger(__name__)


class LightClientProxy:
    def __init__(self, index_html):
        with open(index_html) as fp:
            self.data = fp.read()

    def get(self, url):
        return self.data


class Expensive(Resource):
    method_decorators = [paywall_decorator]

    def __init__(self,
                 channel_manager: ChannelManager,
                 light_client_proxy=None,
                 paywall=None,
                 price: None = None,
                 ) -> None:
        super(Expensive, self).__init__()
        assert isinstance(channel_manager, ChannelManager)
        assert price is None or callable(price) or price > 0
        self.contract_address = channel_manager.channel_manager_contract.address
        self.receiver_address = channel_manager.receiver
        assert is_address(self.contract_address)
        assert is_address(self.receiver_address)
        self.channel_manager = channel_manager
        self.light_client_proxy = light_client_proxy
        self._price = price
        self.paywall = paywall

    def get_paywall(self, url):
        return self.light_client_proxy.get(url)

    def price(self):
        if callable(self._price):
            return self._price()
        else:
            return self._price

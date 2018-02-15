import logging
from flask_restful import Resource
from eth_utils import is_address

from microraiden.channel_manager import (
    ChannelManager,
)
from .paywall_decorator import paywall_decorator

log = logging.getLogger(__name__)


class LightClientProxy:
    """A simple proxy that returns a file that contains paywall html."""
    def __init__(self, index_html: str) -> None:
        with open(index_html) as fp:
            self.data = fp.read()

    def get(self, url: str) -> str:
        return self.data


class Expensive(Resource):
    """Expensive is basically a Flask's resource with a custom method decorator.
    The decorator handles all the payment processing and user just needs to
    implement methods for HTTP verb he intends to use."""
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

    def get_paywall(self, url: str) -> str:
        """Implement this if you want to return a custom HTTP paywall code.

        Returns:
            str: HTML page with the paywall
        """
        return self.light_client_proxy.get(url)

    def price(self) -> int:
        """Implement this if you want to have price set dynamically.

        Returns:
            int: price of a resource. If the value returned is 0, no paywall checks are
                done and the actual content will be sent to the user.
        """
        if callable(self._price):
            return self._price()
        else:
            return self._price

from flask import request
from microraiden.proxy.resources import PaywalledProxyUrl


class PaywalledWikipedia(PaywalledProxyUrl):
    def __init__(self, *args, **kwargs):
        super().__init__(domain='http://en.wikipedia.org', *args, **kwargs)

    def price(self):
        if '/wiki/' in request.path:
            return self._price
        else:
            return 0

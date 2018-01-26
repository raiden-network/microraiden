from microraiden.proxy.resources.expensive import Expensive
from bs4 import BeautifulSoup
import os
import requests
import logging
from flask import Response, stream_with_context, request

from microraiden.constants import MICRORAIDEN_DIR

log = logging.getLogger(__name__)


class PaywalledProxyUrl(Expensive):
    """Proxified paywall - if payment is sucessful,
    it fetches a content from a remote server"""
    def __init__(self, domain=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paywall_html, self.paywall_header = self.extract_paywall_body(
            os.path.join(MICRORAIDEN_DIR, 'microraiden/webui/index.html')
        )
        self.domain = domain

    def extract_paywall_body(self, path):
        # extract body of the paywall page and transform it into a div we'll be
        #  using later
        with open(path) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        b = soup.body
        b['id'] = "overlay"
        b.name = "div"

        h = [el for el in soup.head
             if el.name in ('script', 'style') or
             (el.name == 'link' and 'stylesheet' in el['rel'])]

        return b, h

    def get(self, url, *args, **kwargs):
        req = requests.get(self.domain + url, stream=True, params=request.args)
        return Response(stream_with_context(req.iter_content()),
                        content_type=req.headers['content-type'])

    def get_paywall(self, url: str):
        data = self.get(url)
        if 'text/html' not in data.headers.get('Content-Type'):
            return super().get_paywall(url)

        soup = BeautifulSoup(data.data.decode(), 'html.parser')
        # merge js and css elements
        for tag in reversed(self.paywall_header):
            soup.head.insert(0, tag)

        # inject div that generates the paywall
        soup.body.insert(0, self.paywall_html)

        return str(soup)

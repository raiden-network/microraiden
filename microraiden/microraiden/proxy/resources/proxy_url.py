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
        self.paywall_html = self.extract_paywall_body(
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
        return b

    def get(self, url, *args, **kwargs):
        req = requests.get(self.domain + url, stream=True, params=request.args)
        return Response(stream_with_context(req.iter_content()),
                        content_type=req.headers['content-type'])

    def get_paywall(self, url: str):
        data = self.get(url)
        if data.headers['Content-Type'] != 'text/html':
            return super().get_paywall(url)

#  <link rel="stylesheet" type="text/css" href="/js/styles.css">

        soup = BeautifulSoup(data.data.decode(), 'html.parser')
        # generate js paths that are required
        js_paths = [
            "//code.jquery.com/jquery-3.2.1.js",
            "//cdnjs.cloudflare.com/ajax/libs/js-cookie/2.1.4/js.cookie.min.js",
            "//maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js",
            "/js/web3.js",
            "/js/microraiden.js"]
        for src in js_paths:
            js_tag = soup.new_tag('script', type="text/javascript", src=src)
            soup.head.append(js_tag)
        # generate css
        bs_tag = soup.new_tag('link', rel="stylesheet",
                              type="text/css", href="/js/dark-bootstrap.min.css")
        css_tag = soup.new_tag('link', rel="stylesheet", type="text/css", href="/js/styles.css")
        soup.head.insert(0, bs_tag)
        soup.head.insert(0, css_tag)

        # inject div that generates the paywall
        soup.body.insert(0, self.paywall_html)

        return str(soup)

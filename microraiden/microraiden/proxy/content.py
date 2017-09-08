import os
from flask import make_response, request, Response, stream_with_context
import requests
import re
import mimetypes
import logging
import bs4

from microraiden.config import MICRORAIDEN_DIR

log = logging.getLogger(__name__)


class PaywalledContent:
    """Configuration of a paywalled resource. Pass this to PaywalledProxy.add_resource()
        to register a new path.
        Params:
            path (string): path to a newly created resource (i.e. /expensive/<path:content>)
            price (int)  : price of the resource
            get_fn (callable): function that returns paywalled content
        """
    def __init__(self, path, price, get_fn=lambda _: (200, "OK")):
        assert isinstance(path, str)
        assert isinstance(price, int) or callable(price)
        self.path = path
        self.price = price
        if get_fn is not None:
            assert callable(get_fn)
            self.get_cb = get_fn
        # this is an object that returns paywall proxy html to be sent to the browser
        self.light_client_proxy = None

    def get(self, url):
        return self.get_cb(url)

    def is_paywalled(self, url):
        return True

    def get_paywall(self, request: str, receiver_address: str, price: int, token_address: str):
        assert(self.light_client_proxy is not None)
        return self.light_client_proxy.get(request, receiver_address, price, token_address)


class PaywalledFile(PaywalledContent):
    def __init__(self, path, price, filepath):
        super(PaywalledFile, self).__init__(path, price)
        assert isinstance(filepath, str)
        self.filepath = filepath

    def get(self, url):
        try:
            mimetype = mimetypes.guess_type(self.filepath)
            data = open(self.filepath, 'rb').read()
            headers = {'Content-Type': mimetype[0]}
            return make_response(data, 200, headers)
        except FileNotFoundError:
            return 404, "NOT FOUND"
        except:
            return 500, ""


class PaywalledProxyUrl(PaywalledContent):
    def __init__(self, path, price, domain, paywalled_resources=None):
        super(PaywalledProxyUrl, self).__init__(path, price)
        assert isinstance(path, str)
        assert isinstance(price, int) or callable(price)
        if paywalled_resources is None:
            paywalled_resources = []
        self.path = path
        self.price = price
        self.get_fn = lambda x: x
        self.domain = domain
        self.paywalled_resources = [re.compile(x) for x in paywalled_resources]
        self.paywall_html = self.extract_paywall_body(
            os.path.join(MICRORAIDEN_DIR, 'microraiden/webui/index.html')
        )

    def extract_paywall_body(self, path):
        # extract body of the paywall page and transform it into a div we'll be
        #  using later
        soup = bs4.BeautifulSoup(open(path).read(), "html.parser")
        b = soup.body
        b['id'] = "overlay"
        b.name = "div"
        return b

    def is_paywalled(self, url):
        url = self.get_fn(url)
        for resource in self.paywalled_resources:
            if resource.match(url):
                return True
        return False

    def get(self, url):
        req = requests.get(self.domain + url, stream=True, params=request.args)
        return Response(stream_with_context(req.iter_content()),
                        content_type=req.headers['content-type'])

    def get_paywall(self, request: str, receiver_address: str, price: int, token_address: str):
        data = self.get(request)

#  <link rel="stylesheet" type="text/css" href="/js/styles.css">

        soup = bs4.BeautifulSoup(data.data.decode(), "html.parser")
        # generate js paths that are required
        js_paths = [
            "//code.jquery.com/jquery-3.2.1.js",
            "//cdnjs.cloudflare.com/ajax/libs/js-cookie/2.1.4/js.cookie.min.js",
            "/js/web3.js",
            "/js/microraiden.js"]
        for src in js_paths:
            js_tag = soup.new_tag('script', type="text/javascript", src=src)
            soup.head.insert(0, js_tag)
        # generate css
        bs_tag = soup.new_tag('link', rel="stylesheet",
                              type="text/css", href="/js/dark-bootstrap.min.css")
        css_tag = soup.new_tag('link', rel="stylesheet", type="text/css", href="/js/styles.css")
        soup.head.insert(0, bs_tag)
        soup.head.insert(0, css_tag)

        # inject div that generates the paywall
        soup.body.insert(0, self.paywall_html)

        return str(soup)


class PaywallDatabase:
    def __init__(self):
        self.db = {}

    def get_content(self, url):
        for k, v in self.db.items():
            if re.match(k, url):
                return v
        return None

    def add_content(self, content):
        assert isinstance(content, (PaywalledContent, PaywalledProxyUrl))
        self.db[content.path] = content

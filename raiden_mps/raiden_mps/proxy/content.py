from flask import make_response, request, Response
import requests
import re
import mimetypes


def split_url(url):
    """Splits the given URL into a tuple of (protocol, host, uri)"""
    proto, rest = url.split(':', 1)
    rest = rest[2:].split('/', 1)
    host, uri = (rest[0], rest[1]) if len(rest) == 2 else (rest[0], "")
    return (proto, host, uri)


def proxy_ref_info(request):
    """Parses out Referer info indicating the request is from a previously proxied page.
    For example, if:
        Referer: http://localhost:8080/p/google.com/search?q=foo
    then the result is:
        ("google.com", "search?q=foo")
    """
    ref = request.headers.get('referer')
    if ref:
        _, _, uri = split_url(ref)
        if uri.find("/") < 0:
            return None
        first, rest = uri.split("/", 1)
        if first in "pd":
            parts = rest.split("/", 1)
            r = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
            return r
    return None


def get_source_rsp(url):
        url = 'http://%s' % url
        # Pass original Referer for subsequent resource requests
        proxy_ref = proxy_ref_info(request)
        headers = {"Referer": "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
        # Fetch the URL, and stream it back
        return requests.get(url, stream=True, params=request.args, headers=headers)


class PaywalledContent:
    """Configuration of a paywalled resource. Pass this to PaywalledProxy.add_resource()
        to register a new path.
        Params:
            path (string): path to a newly created resource (i.e. /expensive/<path:content>)
            price (int)  : price of the resource
            get_fn (callable): function that returns paywalled content
        """
    def __init__(self, path, price, get_fn=None):
        assert isinstance(path, str)
        assert isinstance(price, int) or callable(price)
        self.path = path
        self.price = price
        if get_fn is not None:
            assert callable(get_fn)
            self.get = get_fn

    def get(self, request):
        return "OK"


class PaywalledFile(PaywalledContent):
    def __init__(self, path, price, filepath):
        super(PaywalledFile, self).__init__(path, price)
        assert isinstance(filepath, str)
        self.filepath = filepath

    def get(self, request):
        try:
            mimetype = mimetypes.guess_type(self.filepath)
            data = open(self.filepath, 'rb').read()
            headers = {'Content-Type': mimetype[0]}
            return make_response(data, 200, headers)
        except FileNotFoundError:
            return 404, "NOT FOUND"
        except:
            return 500, ""


class PaywalledProxyUrl:
    def __init__(self, path, price):
        assert isinstance(path, str)
        assert isinstance(price, int)
        self.path = path
        self.price = price

    def get(self, request):
        url = request.split('/', 1)[1]
        r = get_source_rsp(url)

        def generate():
            for chunk in r.iter_content(1024):
                yield chunk
        return Response(generate())


class PaywallDatabase:
    def __init__(self):
        self.db = {}

    def get_content(self, url):
        for k, v in self.db.items():
            if re.match(k, url):
                return v
        return None

    def add_content(self, content):
        assert isinstance(content, PaywalledContent) or isinstance(content, PaywalledProxyUrl)
        self.db[content.path] = content

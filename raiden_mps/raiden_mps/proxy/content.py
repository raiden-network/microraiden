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
        assert isinstance(price, int)
        self.path = path
        self.price = price
        if get_fn is not None:
            assert callable(get_fn)
            self.get = get_fn

    def get(self, request):
        return "OK"


class PaywallDatabase:
    def __init__(self):
        self.db = {}

    def get_content(self, url):
        return self.db.get(url, None)

    def add_content(self, content):
        assert isinstance(content, PaywalledContent)
        self.db[content.path] = content

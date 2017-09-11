# to fix requests's SSL infinite recursion bug, SSL must be
# monkeypatched first, and only then requests can be imported
# the bug occurs with Python3.6, requests=2.8.14 and gevent==1.2.2
from gevent import monkey
monkey.patch_ssl()
import requests

from .client import (
    Client,
    HTTPClient,
    DefaultHTTPClient
)

from .header import (
    HTTPHeaders
)

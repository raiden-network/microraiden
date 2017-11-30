import warnings
import requests
import contextlib
import functools


#
# to disable ssl certificate check done by requests library, do:
# with disable_ssl_check():
#    requests.get('https://localhost:5000/')
#
@contextlib.contextmanager
def disable_ssl_check():
    old_request = requests.Session.request
    requests.Session.request = functools.partialmethod(old_request, verify=False)

    warnings.filterwarnings('ignore', 'Unverified HTTPS request')
    yield
    warnings.resetwarnings()

    requests.Session.request = old_request

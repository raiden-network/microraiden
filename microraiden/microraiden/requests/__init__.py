from typing import Callable

from requests import Response
from web3 import Web3

from microraiden import DefaultHTTPClient, Client, HTTPClient
from microraiden.config import CHANNEL_MANAGER_ADDRESS

_http_client = None


def init(
    http_client: HTTPClient = None,
    client: Client = None,
    privkey: str = None,
    key_path: str = None,
    key_password_path: str = None,
    channel_manager_address: str = CHANNEL_MANAGER_ADDRESS,
    web3: Web3 = None,
    retry_interval: float = 5,
    initial_deposit: Callable[[int], int] = lambda price: 10 * price,
    topup_deposit: Callable[[int], int] = lambda price: 5 * price
):
    """
    TODO: document which of these arguments are actually needed in different use cases.
    """
    global _http_client

    if http_client is None:
        if client is None:
            client = Client(
                private_key=privkey,
                key_path=key_path,
                key_password_path=key_password_path,
                channel_manager_address=channel_manager_address,
                web3=web3
            )
        _http_client = DefaultHTTPClient(
            client=client,
            retry_interval=retry_interval,
            initial_deposit=initial_deposit,
            topup_deposit=topup_deposit
        )
    else:
        _http_client = http_client


def _check_init():
    assert _http_client, 'microraiden.requests has not been initialized. ' \
                         'Please call microraiden.requests.init() first.'


def request(method: str, url: str, **kwargs) -> Response:
    _check_init()
    return _http_client.request(method, url, **kwargs)


def head(url: str, **kwargs) -> Response:
    return request('HEAD', url, **kwargs)


def get(url: str, **kwargs) -> Response:
    return request('GET', url, **kwargs)


def post(url: str, **kwargs) -> Response:
    return request('POST', url, **kwargs)


def put(url: str, **kwargs) -> Response:
    return request('PUT', url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    return request('PATCH', url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    return request('DELETE', url, **kwargs)

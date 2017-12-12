import pytest
import logging
import types
from microraiden import DefaultHTTPClient, Client
import microraiden.requests

log = logging.getLogger(__name__)


@pytest.fixture
def default_http_client(client: Client, use_tester: bool):
    # patch request_resource of this instance in order to advance blocks when doing requests
    def request_patched(self: DefaultHTTPClient, method: str, url: str, **kwargs):
        if use_tester:
            log.info('Mining new block.')
            self.client.core.web3.testing.mine(1)
        return DefaultHTTPClient._request_resource(self, method, url, **kwargs)

    http_client = DefaultHTTPClient(client, retry_interval=0.1)
    http_client._request_resource = types.MethodType(request_patched, http_client)
    yield http_client


@pytest.fixture
def init_microraiden_requests(default_http_client: DefaultHTTPClient):
    microraiden.requests.init(http_client=default_http_client)

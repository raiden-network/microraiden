import pytest
import logging
from microraiden import DefaultHTTPClient

log = logging.getLogger(__name__)


@pytest.fixture
def default_http_client(client, api_endpoint, api_endpoint_port):
    # patch request_resource of this instance in order to advance blocks when doing requests
    x = DefaultHTTPClient._request_resource

    def request_patched(self: DefaultHTTPClient):
        if self.client.channel_manager_proxy.tester_mode:
            log.info('Mining new block.')
            self.client.web3.testing.mine(1)
        return x(self)

    DefaultHTTPClient._request_resource = request_patched

    http_client = DefaultHTTPClient(client, api_endpoint, api_endpoint_port, retry_interval=0.5)
    return http_client

import pytest
import logging
import types
from microraiden import DefaultHTTPClient

log = logging.getLogger(__name__)


@pytest.fixture
def default_http_client(client, api_endpoint, api_endpoint_port):
    # patch request_resource of this instance in order to advance blocks when doing requests
    def request_patched(self: DefaultHTTPClient, request: str):
        if self.client.channel_manager_proxy.tester_mode:
            log.info('Mining new block.')
            self.client.web3.testing.mine(1)
        return DefaultHTTPClient._request_resource(self, request)

    http_client = DefaultHTTPClient(client, api_endpoint, api_endpoint_port, retry_interval=0.5)
    http_client._request_resource = types.MethodType(request_patched, http_client)
    return http_client

import pytest
from raiden_mps import DefaultHTTPClient


@pytest.fixture
def default_http_client(client, api_endpoint, api_endpoint_port):
    # patch request_resource of this instance in order to advance blocks when doing requests
    x = DefaultHTTPClient._request_resource

    def request_patched(self: DefaultHTTPClient):
        if self.client.channel_manager_proxy.tester_mode:
            self.client.web3.testing.mine(1)
        return x(self)

    DefaultHTTPClient._request_resource = request_patched

    http_client = DefaultHTTPClient(client, api_endpoint, api_endpoint_port, retry_interval=1)
    return http_client

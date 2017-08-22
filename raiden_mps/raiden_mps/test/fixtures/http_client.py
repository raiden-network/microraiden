import pytest
import types
from raiden_mps import DefaultHTTPClient


@pytest.fixture
def default_http_client(client, api_endpoint, api_endpoint_port):
    http_client = DefaultHTTPClient(client, api_endpoint, api_endpoint_port)
    # patch request_resource of this instance in order to advance blocks when doing requests
    x = DefaultHTTPClient._request_resource

    def request_patched(self):
        self.client.web3.testing.mine(1)
        return x(self)

    http_client._request_resource = types.MethodType(request_patched, http_client)
    return http_client

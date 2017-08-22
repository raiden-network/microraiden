import pytest
from raiden_mps import DefaultHTTPClient


@pytest.fixture
def default_http_client(client, api_endpoint, api_endpoint_port):
    return DefaultHTTPClient(client, api_endpoint, api_endpoint_port)

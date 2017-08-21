import pytest
from raiden_mps.examples.m2m_client import M2MClient


@pytest.fixture
def m2m_client(client, api_endpoint, api_endpoint_port):
    return M2MClient(client, api_endpoint, api_endpoint_port)

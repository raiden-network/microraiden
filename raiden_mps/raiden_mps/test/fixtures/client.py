import pytest
import tempfile
import shutil

from raiden_mps.client.rmp_client import RMPClient
from raiden_mps.client.m2m_client import M2MClient

from ethereum.utils import privtoaddr, encode_hex
from raiden_mps.contract_proxy import ContractProxy, ChannelContractProxy
from raiden_mps.config import GAS_LIMIT


@pytest.fixture
def client_address(client_privkey):
    return '0x' + encode_hex(privtoaddr(client_privkey))


@pytest.fixture
def rpc_endpoint():
    return 'localhost'


@pytest.fixture
def rpc_port():
    return 8545


@pytest.fixture
def datadir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def client_contract_proxy(web3, sender_privkey, channel_manager_contract_address,
                          channel_manager_abi):
    return ChannelContractProxy(web3, sender_privkey,
                                channel_manager_contract_address,
                                channel_manager_abi,
                                int(20e9), GAS_LIMIT)


@pytest.fixture
def client_token_proxy(web3, sender_privkey, token_contract_address, token_abi):
    return ContractProxy(web3, sender_privkey,
                         token_contract_address,
                         token_abi,
                         int(20e9), GAS_LIMIT)


@pytest.fixture
def rmp_client(sender_privkey,
               client_contract_proxy,
               client_token_proxy,
               datadir,
               channel_manager_contract_address,
               token_contract_address):
    return RMPClient(
        privkey=sender_privkey,
        channel_manager_proxy=client_contract_proxy,
        token_proxy=client_token_proxy,
        datadir=datadir,
        channel_manager_address=channel_manager_contract_address,
        token_address=token_contract_address
    )


@pytest.fixture
def m2m_client(rmp_client, api_endpoint, api_endpoint_port):
    return M2MClient(rmp_client,
                     api_endpoint,
                     api_endpoint_port)

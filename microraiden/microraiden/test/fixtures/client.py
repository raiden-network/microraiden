import shutil
import tempfile

import pytest

from microraiden import Client
from microraiden.config import GAS_LIMIT
from microraiden.contract_proxy import ContractProxy, ChannelContractProxy
from microraiden.crypto import privkey_to_addr
from microraiden.test.utils.client import close_all_channels_cooperatively


@pytest.fixture
def client_address(client_privkey):
    return privkey_to_addr(client_privkey)


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
                          channel_manager_abi, use_tester):
    return ChannelContractProxy(
        web3,
        sender_privkey,
        channel_manager_contract_address,
        channel_manager_abi,
        int(20e9), GAS_LIMIT,
        use_tester
    )


@pytest.fixture
def client_token_proxy(web3, sender_privkey, token_contract_address, token_abi, use_tester):
    return ContractProxy(
        web3,
        sender_privkey,
        token_contract_address,
        token_abi,
        int(20e9), GAS_LIMIT,
        use_tester
    )


@pytest.fixture
def client(
        sender_privkey,
        client_contract_proxy,
        client_token_proxy,
        datadir,
        channel_manager_contract_address,
        token_contract_address
):
    client = Client(
        privkey=sender_privkey,
        channel_manager_proxy=client_contract_proxy,
        token_proxy=client_token_proxy,
        datadir=datadir,
        channel_manager_address=channel_manager_contract_address,
        token_address=token_contract_address
    )
    yield client
    client.close()


@pytest.fixture
def clean_channels(client):
    close_all_channels_cooperatively(client, balance=0)
    yield
    close_all_channels_cooperatively(client, balance=0)

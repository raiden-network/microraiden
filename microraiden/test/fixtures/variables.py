import pytest
from eth_utils import encode_hex, remove_0x_prefix
from ethereum.tester import keys

import os
import json
from microraiden.utils import privkey_to_addr
from microraiden.constants import (
    CONTRACTS_ABI_JSON,
    CHANNEL_MANAGER_ABI_NAME,
    TOKEN_ABI_NAME,
)


@pytest.fixture
def proxy_ssl():
    return False


@pytest.fixture
def test_dir(request):
    return request.fspath.dirname


@pytest.fixture
def proxy_ssl_certs(test_dir):
    return os.path.join(test_dir + '/data/key.pem'), os.path.join(test_dir + '/data/cert.pem')


@pytest.fixture(scope='session')
def use_tester(request):
    return request.config.getoption('use_tester')


@pytest.fixture(scope='session')
def clean_channels(request):
    return request.config.getoption('clean_channels')


@pytest.fixture
def api_endpoint():
    """address of a paywall proxy"""
    return 'localhost'


@pytest.fixture
def api_endpoint_port():
    """port the paywall proxy listens on"""
    return 5000


@pytest.fixture
def api_endpoint_address(api_endpoint, api_endpoint_port):
    return api_endpoint + ":" + str(api_endpoint_port)


@pytest.fixture
def init_contract_address():
    return "0x" + "a" * 40


@pytest.fixture(scope='session')
def deployer_privkey():
    return remove_0x_prefix(encode_hex(keys[3]))


@pytest.fixture(scope='session')
def deployer_address(deployer_privkey):
    return privkey_to_addr(deployer_privkey)


@pytest.fixture(scope='session')
def contract_abi_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "../" + CONTRACTS_ABI_JSON)


@pytest.fixture(scope='session')
def contract_abis(contract_abi_path):
    with open(contract_abi_path) as abi_file:
        return json.load(abi_file)


@pytest.fixture(scope='session')
def channel_manager_abi(contract_abis):
    return contract_abis[CHANNEL_MANAGER_ABI_NAME]['abi']


@pytest.fixture(scope='session')
def channel_manager_bytecode(contract_abis):
    return contract_abis[CHANNEL_MANAGER_ABI_NAME]['bytecode']


@pytest.fixture(scope='session')
def token_abi(contract_abis):
    return contract_abis[TOKEN_ABI_NAME]['abi']


@pytest.fixture(scope='session')
def token_bytecode(contract_abis):
    return contract_abis[TOKEN_ABI_NAME]['bytecode']


@pytest.fixture(scope='session')
def kovan_block_time():
    return 4


@pytest.fixture
def state_db_path(tmpdir):
    return ':memory:'
#    db = tmpdir.join("state.db")
#    return db.strpath

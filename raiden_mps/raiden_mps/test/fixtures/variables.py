import pytest
from ethereum.utils import encode_hex, privtoaddr

import os
import json
from raiden_mps.client.rmp_client import CHANNEL_MANAGER_ABI_NAME, TOKEN_ABI_NAME
from raiden_mps.config import (
    TEST_SENDER_PRIVKEY,
    TEST_RECEIVER_PRIVKEY,
    TEST_SECONDARY_RECEIVER_PRIVKEY
)


@pytest.fixture
def contracts_relative_path():
    return 'data/contracts.json'


@pytest.fixture
def compiled_contracts_path(test_dir, contracts_relative_path):
    return os.path.join(test_dir, contracts_relative_path)


@pytest.fixture
def compiled_contracts(compiled_contracts_path):
    return json.load(open(compiled_contracts_path))


@pytest.fixture
def test_dir():
    return os.path.dirname(os.path.dirname(__file__)) + "/../"


@pytest.fixture
def rpc_endpoint():
    return 'localhost'


@pytest.fixture
def rpc_port():
    return 8545


@pytest.fixture
def api_endpoint():
    """address of a paywall proxy"""
    return 'localhost'


@pytest.fixture
def api_endpoint_port():
    """port the paywall proxy listens on"""
    return 5000


@pytest.fixture
def init_contract_address():
    return "0x" + "a" * 40


@pytest.fixture
def manager_state_path():
    return '/tmp/rmp-state.pkl'


@pytest.fixture
def sender_address(sender_privkey):
    return '0x' + encode_hex(privtoaddr(sender_privkey)).decode()


@pytest.fixture
def receiver1_address(receiver1_privkey):
    return '0x' + encode_hex(privtoaddr(receiver1_privkey)).decode()


@pytest.fixture
def receiver2_address(receiver2_privkey):
    return '0x' + encode_hex(privtoaddr(receiver2_privkey)).decode()


@pytest.fixture
def receiver_address(receiver1_address):
    return receiver1_address


@pytest.fixture
def sender_privkey():
    return TEST_SENDER_PRIVKEY


@pytest.fixture
def receiver1_privkey():
    return TEST_RECEIVER_PRIVKEY


@pytest.fixture
def receiver2_privkey():
    return TEST_SECONDARY_RECEIVER_PRIVKEY


@pytest.fixture
def receiver_privkey(receiver1_privkey):
    return receiver1_privkey


@pytest.fixture
def contract_abi_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '../data/contracts.json')


@pytest.fixture
def contract_abis(contract_abi_path):
    abi_file = open(contract_abi_path, 'r')
    return json.load(abi_file)


@pytest.fixture
def channel_manager_abi(contract_abis):
    return contract_abis[CHANNEL_MANAGER_ABI_NAME]['abi']


@pytest.fixture
def token_abi(contract_abis):
    return contract_abis[TOKEN_ABI_NAME]['abi']


@pytest.fixture
def kovan_block_time():
    return 4

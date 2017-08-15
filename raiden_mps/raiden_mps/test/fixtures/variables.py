import pytest
from ethereum.tools.tester import accounts, keys
from ethereum.utils import encode_hex

import os
import json


@pytest.fixture
def compiled_contracts_path():
    return os.path.join(test_dir, contracts_relative_path)


@pytest.fixture
def compiled_contracts(compiled_contracts_path):
    return json.load(open(compiled_contracts_path))


@pytest.fixture
def test_dir():
    return os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def contracts_relative_path():
    return 'data/contracts.json'


@pytest.fixture
def init_contract_address():
    return "0x" + "a" * 40


@pytest.fixture
def manager_state_path():
    return '/tmp/rmp-state.pkl'


@pytest.fixture
def sender_address():
    return encode_hex(accounts[0]).decode()


@pytest.fixture
def receiver_address():
    return encode_hex(accounts[1]).decode()


@pytest.fixture
def sender_privkey():
    return encode_hex(keys[0]).decode()


@pytest.fixture
def receiver_privkey():
    return encode_hex(keys[1]).decode()

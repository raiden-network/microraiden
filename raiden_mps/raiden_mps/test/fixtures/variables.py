import pytest

@pytest.fixture
def init_contract_address():
    return "0x" + "a" * 40

@pytest.fixture
def manager_state_path():
    return '/tmp/rmp-state.pkl'

from typing import List

import pytest
from web3 import Web3

from microraiden import Client
from microraiden.utils import privkey_to_addr
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
def datadir(tmpdir):
    return tmpdir.strpath + "client"


@pytest.fixture
def client(
        sender_privkey: str,
        channel_manager_address: str,
        web3: Web3,
        clean_channels: bool,
        private_keys: List[str],
        patched_contract,
        revert_chain
):
    client = Client(
        private_key=sender_privkey,
        channel_manager_address=channel_manager_address,
        web3=web3
    )
    if clean_channels:
        close_all_channels_cooperatively(
            client,
            private_keys,
            channel_manager_address,
        )

    yield client

    if clean_channels:
        close_all_channels_cooperatively(
            client,
            private_keys,
            channel_manager_address,
        )

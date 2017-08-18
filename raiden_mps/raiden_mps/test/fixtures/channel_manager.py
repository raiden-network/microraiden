import logging
import pytest
import gevent
from populus.utils.wait import wait_for_transaction_receipt
from populus.wait import Wait
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.channel_manager import ChannelManager
from web3 import Web3
from web3.providers.rpc import RPCProvider
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS, TOKEN_ADDRESS
from raiden_mps.client.rmp_client import GAS_PRICE, GAS_LIMIT


def check_succesful_tx(web3, txid, timeout=180):
    """See if transaction went through (Solidity code did not throw).
    :return: Transaction receipt
    """
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt


@pytest.fixture(scope='session', autouse=True)
def disable_requests_loggin():
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


@pytest.fixture
def channel_manager_contract_address():
    return CHANNEL_MANAGER_ADDRESS


@pytest.fixture
def token_contract_address():
    return TOKEN_ADDRESS


@pytest.fixture
def web3(rpc_endpoint, rpc_port):
    rpc = RPCProvider(rpc_endpoint, rpc_port)
    return Web3(rpc)


@pytest.fixture
def wait(web3, kovan_block_time):
    poll_interval = kovan_block_time / 2
    return Wait(web3, poll_interval=poll_interval)


@pytest.fixture
def wait_for_blocks(web3, kovan_block_time):
    def wait_for_blocks(n):
        target_block = web3.eth.blockNumber + n
        while web3.eth.blockNumber < target_block:
            gevent.sleep(kovan_block_time / 2)
    return wait_for_blocks


@pytest.fixture
def channel_manager_contract_proxy1(web3, receiver1_privkey, channel_manager_contract_address,
                                    channel_manager_abi):
    return ChannelContractProxy(web3, receiver1_privkey, channel_manager_contract_address,
                                channel_manager_abi, GAS_PRICE, GAS_LIMIT)


@pytest.fixture
def channel_manager_contract_proxy2(web3, receiver2_privkey, channel_manager_contract_address,
                                    channel_manager_abi):
    return ChannelContractProxy(web3, receiver2_privkey, channel_manager_contract_address,
                                channel_manager_abi, GAS_PRICE, GAS_LIMIT)


@pytest.fixture
def channel_manager_contract_proxy(channel_manager_contract_proxy1):
    return channel_manager_contract_proxy1


@pytest.fixture
def channel_manager1(web3, channel_manager_contract_proxy1, receiver_address, receiver_privkey):
    # disable logging during sync
    logging.getLogger('channel_manager').setLevel(logging.WARNING)
    channel_manager = ChannelManager(web3,
                                     channel_manager_contract_proxy1,
                                     receiver_address,
                                     receiver_privkey)
    channel_manager.start()
    channel_manager.wait_sync()
    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    return channel_manager


@pytest.fixture
def channel_manager2(web3, channel_manager_contract_proxy2, receiver2_address, receiver2_privkey):
    # disable logging during sync
    logging.getLogger('channel_manager').setLevel(logging.WARNING)
    channel_manager = ChannelManager(web3,
                                     channel_manager_contract_proxy2,
                                     receiver2_address,
                                     receiver2_privkey)
    channel_manager.start()
    channel_manager.wait_sync()
    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    return channel_manager


@pytest.fixture
def channel_manager(channel_manager1):
    return channel_manager1

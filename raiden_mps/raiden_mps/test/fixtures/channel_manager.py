import pytest
from populus.utils.wait import wait_for_transaction_receipt
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
def channel_manager_contract_proxy(web3, receiver_privkey, channel_manager_contract_address,
                                   channel_manager_abi):
    return ChannelContractProxy(web3, receiver_privkey, channel_manager_contract_address,
                                channel_manager_abi, GAS_PRICE, GAS_LIMIT)


@pytest.fixture
def channel_manager(web3, channel_manager_contract_proxy, receiver_address, receiver_privkey):
    return ChannelManager(web3,
                          channel_manager_contract_proxy,
                          receiver_address,
                          receiver_privkey)

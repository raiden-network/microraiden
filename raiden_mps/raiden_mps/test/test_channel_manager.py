import json
import os
import pytest
from populus.project import Project
from populus.utils.wait import wait_for_transaction_receipt
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.channel_manager import ChannelManager



def check_succesful_tx(web3, txid, timeout=180):
    """See if transaction went through (Solidity code did not throw).
    :return: Transaction receipt
    """
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt


@pytest.fixture
def chain():
    project = Project()
    project.is_compiled_contract_cache_stale = lambda: False
    project.fill_contracts_cache(compiled_contracts, 0)
    with project.get_chain('testrpc') as chain:
        yield chain


@pytest.fixture
def web3(chain):
    return chain.web3


@pytest.fixture
def contracts(web3, chain, sender_address):
    # deploy contracts
    token_contract_data = compiled_contracts['RDNToken']
    token_factory = web3.eth.contract(
        contract_name='RDNToken',
        abi=token_contract_data["abi"],
        bytecode=token_contract_data["bytecode"],
        bytecode_runtime=token_contract_data["bytecode_runtime"]
    )
    txhash = token_factory.deploy(args=[10000, "RDNToken", 6, "RDN"])
    receipt = check_succesful_tx(chain.web3, txhash, 250)
    token_addr = receipt["contractAddress"]
    token_contract = token_factory(token_addr)

    channel_contract_data = compiled_contracts['RaidenMicroTransferChannels']
    channel_factory = web3.eth.contract(
        contract_name='RaidenMicroTransferChannels',
        abi=channel_contract_data["abi"],
        bytecode=channel_contract_data["bytecode"],
        bytecode_runtime=channel_contract_data["bytecode_runtime"]
    )
    txhash = channel_factory.deploy(args=[token_addr, 100])
    receipt = check_succesful_tx(chain.web3, txhash, 250)
    cf_address = receipt["contractAddress"]
    channel_contract = channel_factory(cf_address)

    # send RDNTokens to sender
    token_contract.transact({"from": web3.eth.accounts[0]}).transfer(sender_address, 400)

    return token_contract, channel_contract


@pytest.fixture
def token_contract(contracts):
    return contracts[0]


@pytest.fixture
def channel_manager_contract_proxy(contracts, receiver_privkey):
    contract = contracts[1]
    pytest.set_trace()
    contract_proxy = ChannelContractProxy(contract.web3, receiver_privkey, contract.address,
                                          contract.abi, int(20e9), 50000)
    return contracts[1]


@pytest.fixture
def channel_manager(channel_manager_contract, receiver_account):
    channel_manager = ChannelManager()


def test_channel_opening(channel_manager_contract_proxy, sender_account, receiver_account):
    pass

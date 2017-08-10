import json
import os
import pytest
from populus.project import Project
from populus.utils.wait import wait_for_transaction_receipt
from populus.contracts.contract import construct_contract_factory
from raiden_mps.channel_manager import ChannelManager


test_dir = os.path.dirname(os.path.dirname(__file__))
contracts_relative_path = 'data/contracts.json'
compiled_contracts_path = os.path.join(test_dir, contracts_relative_path)
compiled_contracts = json.load(open(compiled_contracts_path))


def check_succesful_tx(web3, txid, timeout=180):
    """See if transaction went through (Solidity code did not throw).
    :return: Transaction receipt
    """
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt

@pytest.fixture
def sender():
    return '0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1'  # funded default account of testrpc


@pytest.fixture
def receiver():
    return '0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e'  # funded default account of testrpc


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
def contracts(web3, chain, sender):
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
        contract_name='RDNToken',
        abi=channel_contract_data["abi"],
        bytecode=channel_contract_data["bytecode"],
        bytecode_runtime=channel_contract_data["bytecode_runtime"]
    )
    txhash = channel_factory.deploy(args=[token_addr, 100])
    receipt = check_succesful_tx(chain.web3, txhash, 250)
    cf_address = receipt["contractAddress"]
    channel_contract = channel_factory(cf_address)

    # send RDNTokens to sender
    token_contract.transact({"from": web3.eth.accounts[0]}).transfer(sender, 400)

    return token_contract, channel_contract


def test_channel_opening(contracts, sender, receiver):
    pass

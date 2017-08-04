import pytest
from populus.utils.wait import wait_for_transaction_receipt
from web3.utils.compat import (
    Timeout,
)
from ethereum import tester
import sign

@pytest.fixture
def contract(chain, accounts):
    global token;
    (A, B, C) = accounts(3)
    RDNToken = chain.provider.get_contract_factory('RDNToken')
    deploy_txn_hash = RDNToken.deploy(args=[10000, "RDN", 2, "R"])
    token = chain.wait.for_contract_address(deploy_txn_hash)
    RaidenPaymentChannel = chain.provider.get_contract_factory('RaidenPaymentChannel')
    deploy_txn_hash = RaidenPaymentChannel.deploy(args=[])
    address = chain.wait.for_contract_address(deploy_txn_hash)
    RDNToken(token).transact({"from": A}).approve(address, 100)
    assert RDNToken(token).call().balanceOf(address) == 0
    contract = RaidenPaymentChannel(address)
    contract.transact({"from": A}).init(B, token, 100, 10);
    assert RDNToken(token).call().balanceOf(address) == 100
    return contract


@pytest.fixture
def accounts(web3):
    def get(num):
        return [web3.eth.accounts[i] for i in range(num)]
    return get


def print_gas_used(web3, trxid, message):
    receipt = wait_for_transaction_receipt(web3, trxid)
    print(message, receipt["gasUsed"])


def wait(transfer_filter):
    with Timeout(30) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)


def test_open_channel(contract, accounts):
    (A, B, C) = accounts(3)
    id = contract.call().getChannel(A, B, token)
    assert id[1] != "0x0000000000000000000000000000000000000000"


def test_sign_message_and_settlement(contract, accounts, chain):
    (A, B, C) = accounts(3)
    # call helper function to get sha3 of sender, receiver, token, balance
    data = contract.call().shaOfValue(A, B, token, 90)
    # get channel data
    id  = contract.call().getChannel(A, B, token)
    # check that sender is set and therefore channel has been created
    assert id[1] != "0x0000000000000000000000000000000000000000"
    # sign the message with the private key of account A (which equals sender here)
    sig, addr = sign.check(bytes(data, "raw_unicode_escape"), tester.k0)
    # get the token to check for balance after channel close
    RDNToken = chain.provider.get_contract_factory('RDNToken')
    # close the channel (and settle afterwards since caller is receiver account B)
    contract.transact({"from":B}).close(id[0], 90, sig);
    # get the channel which should be removed now
    id  = contract.call().getChannel(A, B, token)
    assert id[1] == "0x0000000000000000000000000000000000000000"
    # check the balances of contract and sender (account A) and receiver (account B)
    assert RDNToken(token).call().balanceOf(contract.address) == 0
    assert RDNToken(token).call().balanceOf(A) == 9910
    assert RDNToken(token).call().balanceOf(B) == 90

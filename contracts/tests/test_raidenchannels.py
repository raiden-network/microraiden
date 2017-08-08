import pytest
from populus.utils.wait import wait_for_transaction_receipt
from web3.utils.compat import (
    Timeout,
)
from ethereum import tester
import sign


@pytest.fixture
def contract(chain, accounts):
    global token
    global logs
    logs = {}
    (A, B, C) = accounts(3)
    RDNToken = chain.provider.get_contract_factory('RDNToken')
    deploy_txn_hash = RDNToken.deploy(args=[10000, "RDN", 2, "R"])
    token_address = chain.wait.for_contract_address(deploy_txn_hash)
    token = RDNToken(token_address)

    RaidenMicroTransferChannels = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
    deploy_txn_hash = RaidenMicroTransferChannels.deploy(args=[token_address, 100])
    address = chain.wait.for_contract_address(deploy_txn_hash)
    print('RaidenMicroTransferChannels contract address', address)

    contract = RaidenMicroTransferChannels(address)
    return contract


@pytest.fixture
def channel(contract, accounts):
    (A, B) = accounts(2)

    token.transact({"from": A}).approve(contract.address, 100)
    assert token.call().balanceOf(contract.address) == 0
    contract.transact({"from": A}).createChannel(B, 100)
    assert token.call().balanceOf(contract.address) == 100

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    log_args = logs['ChannelCreated'][0]['args']
    open_block_number = log_args['open_block_number']

    return (A, B, open_block_number)



@pytest.fixture
def accounts(web3):
    def get(num):
        return [web3.eth.accounts[i] for i in range(num)]
    return get


def save_logs(contract, event_name):
    logs[event_name] = []

    def add(log):
        logs[event_name].append(log)

    transfer_filter_past = contract.pastEvents(event_name)
    past_events = transfer_filter_past.get()
    for event in past_events:
        add(event)

    transfer_filter = contract.on(event_name)
    # wait(transfer_filter)
    events = transfer_filter.get()
    for event in events:
        add(event)
    transfer_filter.watch(lambda x: add(x))


def print_gas_used(web3, trxid, message):
    receipt = wait_for_transaction_receipt(web3, trxid)
    print(message, receipt["gasUsed"])


def wait(transfer_filter):
    with Timeout(30) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)


def test_open_channel(contract, accounts):
    (A, B) = accounts(2)

    token.transact({"from": A}).approve(contract.address, 100)
    assert token.call().balanceOf(contract.address) == 0
    contract.transact({"from": A}).createChannel(B, 100)
    assert token.call().balanceOf(contract.address) == 100

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    print('--LOGS', logs)
    log_args = logs['ChannelCreated'][0]['args']
    open_block_number = log_args['open_block_number']

    print('open_block_number', open_block_number)

    channel_data = contract.call().getChannel(A, B, open_block_number)
    print('--channel_data', channel_data)
    assert channel_data[1] == 100
    assert channel_data[2] == open_block_number
    assert channel_data[3] == 0


def test_fund_channel(contract, channel):
    (sender, receiver, open_block_number) = channel
    print('test_fund_channel', sender, receiver, open_block_number)

    contract.transact({'from': sender}).fundChannel(receiver, open_block_number, 10)

    channel_data = contract.call().getChannel(sender, receiver, open_block_number)
    assert channel_data[1] == 110


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
    assert token.call().balanceOf(contract.address) == 0
    assert token.call().balanceOf(A) == 9910
    assert token.call().balanceOf(B) == 90

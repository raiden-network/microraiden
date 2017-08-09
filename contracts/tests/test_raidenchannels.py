import pytest
from populus.utils.wait import wait_for_transaction_receipt
from web3.utils.compat import (
    Timeout,
)
from ethereum import tester
import sign


def print_logs(contract, event, name=''):
    transfer_filter_past = contract.pastEvents(event)
    past_events = transfer_filter_past.get()
    if len(past_events):
        print('--(', name, ') past events for ', event, past_events)

    transfer_filter = contract.on(event)
    events = transfer_filter.get()
    if len(events):
        print('--(', name, ') events for ', event, events)

    transfer_filter.watch(lambda x: print('--(', name, ') event ', event, x['args']))



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

    print_logs(token, 'Approval', 'RDNToken')
    print_logs(token, 'Transfer', 'RDNToken')

    RaidenMicroTransferChannels = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
    deploy_txn_hash = RaidenMicroTransferChannels.deploy(args=[token_address, 5])
    address = chain.wait.for_contract_address(deploy_txn_hash)
    print('RaidenMicroTransferChannels contract address', address)

    contract = RaidenMicroTransferChannels(address)

    print_logs(contract, 'ChannelCreated', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelCloseRequested', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelSettled', 'RaidenMicroTransferChannels')

    return contract


@pytest.fixture
def channel(contract, accounts):
    (A, B, C) = accounts(3)

    token.transact({"from": A}).transfer(B, 100)
    token.transact({"from": B}).approve(contract.address, 100)
    assert token.call().balanceOf(contract.address) == 0
    contract.transact({"from": B}).createChannel(C, 100)
    assert token.call().balanceOf(contract.address) == 100

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    open_block_number = logs['ChannelCreated'][0]['blockNumber']

    return (B, C, open_block_number)


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


def test_key_hash(contract, channel):
    (sender, receiver, open_block_number) = channel
    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)

    assert channel_data[0] == contract.call().getKey(sender, receiver, open_block_number)


def test_open_channel(web3, contract, accounts):
    (A, B) = accounts(2)

    token.transact({"from": A}).approve(contract.address, 100)
    assert token.call().balanceOf(contract.address) == 0

    contract.transact({"from": A}).createChannel(B, 100)

    assert token.call().balanceOf(contract.address) == 100
    assert token.call().allowance(A, contract.address) == 0

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    open_block_number = logs['ChannelCreated'][0]['blockNumber']

    channel_data = contract.call().getChannelInfo(A, B, open_block_number)

    assert channel_data[1] == 100
    assert channel_data[2] == open_block_number
    assert channel_data[3] == 0


def test_fund_channel(contract, channel):
    (sender, receiver, open_block_number) = channel

    contract.transact({'from': sender}).topUp(receiver, open_block_number, 10)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == 110


def test_close_by_receiver(contract, channel):
    (sender, receiver, open_block_number) = channel

    balance = 40
    deposit = 100

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = deposit - balance
    contract_post_balance = contract_pre_balance - deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance


def test_close_by_sender(web3, contract, channel):
    (sender, receiver, open_block_number) = channel

    balance = 40
    deposit = 100

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)
    balance_msg_sig_false, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k2)

    balance_msg_sig_hash = contract.call().closingAgreementMessageHash(balance_msg_sig)
    balance_msg_sig_hash_false = contract.call().closingAgreementMessageHash(balance_msg_sig_false)

    closing_sig, addr = sign.check(bytes(balance_msg_sig_hash, "raw_unicode_escape"), tester.k2)
    closing_sig_false, addr = sign.check(bytes(balance_msg_sig_hash, "raw_unicode_escape"), tester.k1)
    closing_sig_false2, addr = sign.check(bytes(balance_msg_sig_hash_false, "raw_unicode_escape"), tester.k2)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    with pytest.raises(ValueError):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false2)

    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = deposit - balance
    contract_post_balance = contract_pre_balance - deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance


def test_close_by_sender_challenge_settle_by_receiver(web3, contract, channel):
    (sender, receiver, open_block_number) = channel

    balance = 40
    deposit = 100

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[3] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number, balance)

    contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = deposit - balance
    contract_post_balance = contract_pre_balance - deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance


def test_close_by_sender_challenge_settle_by_sender(web3, contract, channel):
    (sender, receiver, open_block_number) = channel

    balance = 40
    deposit = 100

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[3] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number, balance)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number, balance)

    web3.testing.mine(6)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number, balance)

    contract.transact({'from': sender}).settle(receiver, open_block_number, balance)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = deposit - balance
    contract_post_balance = contract_pre_balance - deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

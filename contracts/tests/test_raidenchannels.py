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
def contract(chain, web3):
    global token
    global logs
    global challenge_period
    challenge_period = 5
    logs = {}
    (A, B, C) = web3.eth.accounts[:3]
    RDNToken = chain.provider.get_contract_factory('RDNToken')
    deploy_txn_hash = RDNToken.deploy(args=[10000, "RDN", 2, "R"])
    token_address = chain.wait.for_contract_address(deploy_txn_hash)
    token = RDNToken(token_address)

    print_logs(token, 'Approval', 'RDNToken')
    print_logs(token, 'Transfer', 'RDNToken')

    RaidenMicroTransferChannels = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
    deploy_txn_hash = RaidenMicroTransferChannels.deploy(args=[token_address, challenge_period])
    address = chain.wait.for_contract_address(deploy_txn_hash)
    print('RaidenMicroTransferChannels contract address', address)

    contract = RaidenMicroTransferChannels(address)

    print_logs(contract, 'ChannelCreated', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelToppedUp', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelCloseRequested', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelSettled', 'RaidenMicroTransferChannels')

    return contract


@pytest.fixture
def channel(contract, web3):
    (Owner, B, C) = web3.eth.accounts[:3]
    global channel_deposit
    channel_deposit = 220

    token.transact({"from": Owner}).transfer(B, channel_deposit + 50)
    token.transact({"from": Owner}).transfer(B, channel_deposit + 50)

    token.transact({"from": B}).approve(contract.address, channel_deposit)
    assert token.call().balanceOf(contract.address) == 0
    contract.transact({"from": B}).createChannel(C, channel_deposit)
    assert token.call().balanceOf(contract.address) == channel_deposit

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    open_block_number = logs['ChannelCreated'][0]['blockNumber']

    return (B, C, open_block_number)


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


def get_current_deposit(contract, channel):
    (sender, receiver, open_block_number) = channel
    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    return channel_data[1]


def channel_settle_tests(contract, channel):
    (sender, receiver, open_block_number) = channel
    # Approve token allowance
    token.transact({"from": sender}).approve(contract.address, 33)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUp(receiver, open_block_number, 33)


def channel_pre_close_tests(contract, channel):
    (sender, receiver, open_block_number) = channel
    # Approve token allowance
    token.transact({"from": sender}).approve(contract.address, 33)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    contract.transact({'from': sender}).topUp(receiver, open_block_number, 14)


def test_get_channel_info(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    A = web3.eth.accounts[3]
    print(sender, receiver, open_block_number, A)
    with pytest.raises(tester.TransactionFailed):
        contract.call().getChannelInfo(sender, receiver, open_block_number-2)
    web3.testing.mine(2)
    with pytest.raises(tester.TransactionFailed):
        contract.call().getChannelInfo(A, receiver, open_block_number)
    web3.testing.mine(2)
    with pytest.raises(tester.TransactionFailed):
        contract.call().getChannelInfo(sender, A, open_block_number)
    web3.testing.mine(2)
    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[0] == contract.call().getKey(sender, receiver, open_block_number)
    assert channel_data[1] != 0
    assert channel_data[2] == 0
    assert channel_data[3] == 0


def test_channel_create(web3, contract):
    (Owner, A, B, C, D) = web3.eth.accounts[:5]
    depozit_B = 100
    depozit_D = 120

    # Fund accounts with tokens
    token.transact({"from": Owner}).transfer(B, depozit_B)
    token.transact({"from": Owner}).transfer(D, depozit_D)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({"from": B}).createChannel(A, depozit_B)

    # Approve token allowance
    token.transact({"from": B}).approve(contract.address, depozit_B)

    with pytest.raises(TypeError):
        contract.transact({"from": B}).createChannel(A, -2)

    # Cannot create a channel if tokens were not approved
    with pytest.raises(tester.TransactionFailed):
        contract.transact({"from": D}).createChannel(C, depozit_D)

    assert token.call().balanceOf(contract.address) == 0
    pre_balance_B = token.call().balanceOf(B)

    # Create channel
    contract.transact({"from": B}).createChannel(A, depozit_B)

    # Check balances
    assert token.call().balanceOf(contract.address) == depozit_B
    assert token.call().allowance(B, contract.address) == 0
    assert token.call().balanceOf(B) == pre_balance_B - depozit_B

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    open_block_number = logs['ChannelCreated'][0]['blockNumber']

    channel_data = contract.call().getChannelInfo(B, A, open_block_number)
    print('-- --- -- channel_data', channel_data)
    assert channel_data[1] == 100  # deposit
    assert channel_data[2] == 0  # settle_block_number
    assert channel_data[3] == 0  # closing_balance


def test_channel_topup(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]
    top_up_deposit = 14

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUp(receiver, open_block_number, top_up_deposit)

    # Approve token allowance
    token.transact({"from": sender}).approve(contract.address, top_up_deposit)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': A}).topUp(receiver, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUp(A, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUp(receiver, open_block_number, 0)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUp(receiver, 0, top_up_deposit)

    contract.transact({'from': sender}).topUp(receiver, open_block_number, top_up_deposit)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit


def test_close_call(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]
    balance = channel_deposit - 10
    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    # Cannot close what was not opened
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': A}).close(receiver, open_block_number, balance, balance_msg_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(A, open_block_number, balance, balance_msg_sig)

    # Cannot close if arguments not correct
    with pytest.raises(ValueError):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance)
    with pytest.raises(ValueError):
        contract.transact({'from': receiver}).close(receiver, open_block_number, balance)


def test_close_by_receiver(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    channel_pre_close_tests(contract, channel)
    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)
    balance_msg_sig_false, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k2)

    balance_msg_sig_hash = contract.call().closingAgreementMessageHash(balance_msg_sig)
    balance_msg_sig_hash_false = contract.call().closingAgreementMessageHash(balance_msg_sig_false)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': A}).close(receiver, open_block_number, balance, balance_msg_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).close(receiver, open_block_number + 1, balance, balance_msg_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).close(receiver, open_block_number, balance + 1, balance_msg_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig_false)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)


def test_close_by_sender(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)
    balance_msg_sig_false, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k3)

    balance_msg_sig_hash = contract.call().closingAgreementMessageHash(balance_msg_sig)
    balance_msg_sig_hash_false = contract.call().closingAgreementMessageHash(balance_msg_sig_false)

    closing_sig, addr = sign.check(bytes(balance_msg_sig_hash, "raw_unicode_escape"), tester.k2)
    closing_sig_false, addr = sign.check(bytes(balance_msg_sig_hash, "raw_unicode_escape"), tester.k3)
    closing_sig_false2, addr = sign.check(bytes(balance_msg_sig_hash_false, "raw_unicode_escape"), tester.k2)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(A, open_block_number, balance, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number - 3, balance, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance + 5, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig_hash_false, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false2)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)


def test_close_by_sender_challenge_settle_by_receiver(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)


def test_close_by_sender_challenge_settle_by_sender(web3, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = contract.call().balanceMessageHash(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(bytes(balance_msg, "raw_unicode_escape"), tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    web3.testing.mine(challenge_period + 1)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    contract.transact({'from': sender}).settle(receiver, open_block_number)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

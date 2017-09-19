import pytest
import os
from web3.utils.compat import (
    Timeout,
)

from ethereum import tester
import sign

from fixtures import (
    create_contract,
    contract,
    token_contract,
    channels_contract,
    save_logs,
    print_logs,
    get_gas_used,
    print_gas_used,
    get_balance_message,
    decimals
)

import json

global logs
logs = {}


'''
from ethereum.abi import (
    ContractTranslator
)


abi = get_contract_abi()
ct = ContractTranslator(abi)
txdata = ct.encode('createChannel', [B, A, depozit_B])
print('---txdata', txdata)
'''


def get_contract_abi():
    contracts_abi_path = os.path.join(os.path.dirname(__file__), '../build/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    return abi


def add_logs(contract, event_name):
    logs[event_name] = []
    def add(log):
        logs[event_name].append(log)
    save_logs(contract, event_name, add)
    with Timeout(20) as timeout:
        timeout.sleep(2)


def get_current_deposit(contract, channel):
    (sender, receiver, open_block_number) = channel
    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    return channel_data[1]


def get_last_open_block_number(contract):
    add_logs(contract, 'ChannelCreated')
    created_logs = logs['ChannelCreated'][len(logs['ChannelCreated']) - 1]
    open_block_number = created_logs['blockNumber']
    return open_block_number


def channel_post_create_tests(contract, sender, receiver, channel_deposit):
    open_block_number = get_last_open_block_number(contract)
    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)

    assert channel_data[0] == contract.call().getKey(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit
    assert channel_data[2] == 0
    assert channel_data[3] == 0


def channel_settle_tests_20(contract, channel_20):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    token.transact({"from": sender}).approve(contract.address, 33)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUpERC20(receiver, open_block_number, 33)


def channel_pre_close_tests_20(contract, channel_20):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    token.transact({"from": sender}).approve(contract.address, 33)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    contract.transact({'from': sender}).topUpERC20(receiver, open_block_number, 14)


def channel_settle_tests(contract, channel):
    (sender, receiver, open_block_number) = channel


def channel_pre_close_tests(contract, channel):
    (sender, receiver, open_block_number) = channel


@pytest.fixture
def contract(chain, web3, token_contract, channels_contract, decimals):
    global token
    global logs
    global challenge_period
    challenge_period = 5
    logs = {}
    supply = 10000 * 10**(decimals)
    token = token_contract([supply, "ERC223Token", decimals, "TKN"])
    contract = channels_contract([token.address, challenge_period])
    return contract


@pytest.fixture
def channel_20(contract, web3):
    (Owner, B, C) = web3.eth.accounts[:3]
    global channel_deposit
    channel_deposit = 220

    token.transact({"from": Owner}).transfer(B, channel_deposit + 50)
    token.transact({"from": Owner}).transfer(B, channel_deposit + 50)

    token.transact({"from": B}).approve(contract.address, channel_deposit)
    assert token.call().balanceOf(contract.address) == 0
    contract.transact({"from": B}).createChannelERC20(C, channel_deposit)
    assert token.call().balanceOf(contract.address) == channel_deposit

    open_block_number = get_last_open_block_number(contract)

    return (B, C, open_block_number)


@pytest.fixture
def channel(contract, web3):
    (Owner, A, B) = web3.eth.accounts[:3]
    global channel_deposit
    channel_deposit = 220

    txdata = B[2:].zfill(40)
    txdata = bytes.fromhex(txdata)

    print('Owner', Owner)
    print('sender', A)
    print('receiver', B)
    print('ChannelsContract', contract.address)
    print('Token', token.address)

    token.transact({"from": Owner}).transfer(A, channel_deposit + 45)
    token.transact({"from": Owner}).transfer(B, 22)

    # Create channel
    token.transact({"from": A}).transfer(contract.address, channel_deposit, txdata)
    assert token.call().balanceOf(contract.address) == channel_deposit
    open_block_number = get_last_open_block_number(contract)

    return (A, B, open_block_number)


def test_channel_223_create(web3, chain, contract, channels_contract):
    (Owner, A, B, C, D) = web3.eth.accounts[:5]
    other_contract = channels_contract([token.address, 10], {'from': D})
    depozit_B = 100
    depozit_D = 120

    # Allocate some tokens first
    token.transact({"from": Owner}).transfer(B, depozit_B)
    token.transact({"from": Owner}).transfer(D, depozit_D)
    assert token.call().balanceOf(B) == depozit_B
    assert token.call().balanceOf(D) == depozit_D
    assert token.call().balanceOf(contract.address) == 0

    # address - 20 bytes
    txdata = A[2:].zfill(40)
    print('----A', A, txdata)
    txdata = bytes.fromhex(txdata)


    #with pytest.raises(tester.TransactionFailed):
    #    token.transact({"from": B}).transfer(other_contract.address, depozit_B, txdata)
    with pytest.raises(TypeError):
        token.transact({"from": B}).transfer(contract.address, -2, txdata)

    # TODO should this fail?
    #token.transact({"from": B}).transfer(contract.address, depozit_B, A_bytes_fake)
    #A_bytes = '0x829bd824b016326a401d083b33d092293333a830'
    trxid = token.transact({"from": B}).transfer(contract.address, depozit_B, txdata)

    channel_post_create_tests(contract, B, A, depozit_B)

    print('----------------------------------')
    print('GAS USED test_channel_223_create', get_gas_used(chain, trxid))
    print('----------------------------------')


def test_channel_topup_223(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]
    top_up_deposit = 14

    # address 20 bytes
    # padded block number from uint32 (4 bytes) to 32 bytes
    top_up_data = receiver[2:].zfill(40) + hex(open_block_number)[2:].zfill(8)
    print('---top_up_data', top_up_data)
    top_up_data = bytes.fromhex(top_up_data)

    top_up_data_wrong_receiver = A[2:].zfill(64) + hex(open_block_number)[2:].zfill(8)

    top_up_data_wrong_block = receiver[2:].zfill(64) + hex(open_block_number+30)[2:].zfill(8)

    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(contract.address, 0, top_up_data)
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(contract.address, top_up_deposit, top_up_data_wrong_receiver)
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(contract.address, top_up_deposit, top_up_data_wrong_block)

    # Call Token - this calls contract.tokenFallback
    trxid = token.transact({"from": sender}).transfer(contract.address, top_up_deposit, top_up_data)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print('----------------------------------')
    print('GAS USED test_channel_topup_223', get_gas_used(chain, trxid))
    print('----------------------------------')


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


def test_close_call(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]
    balance = channel_deposit - 10

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)

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


def test_close_by_receiver(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    channel_pre_close_tests(contract, channel)
    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)
    balance_msg_sig_false, addr = sign.check(balance_msg, tester.k2)


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

    print('--BALANCES', receiver_pre_balance, sender_pre_balance, contract_pre_balance)

    trxid = contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

    print('----------------------------------')
    print('GAS USED test_close_by_receiver', get_gas_used(chain, trxid))
    print('----------------------------------')


def test_close_by_sender(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_false_receiver = get_balance_message(A, open_block_number, balance)

    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)
    balance_msg_sig_false_signer, addr = sign.check(balance_msg, tester.k3)
    balance_msg_sig_false_receiver, addr = sign.check(balance_msg_false_receiver, tester.k3)

    closing_sig, addr = sign.check(balance_msg, tester.k2)
    closing_sig_false_signer, addr = sign.check(balance_msg, tester.k3)
    closing_sig_false_receiver, addr = sign.check(balance_msg_false_receiver, tester.k2)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(A, open_block_number, balance, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number - 3, balance, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance + 5, balance_msg_sig, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig_false_signer, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig_false_receiver, closing_sig)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false_signer)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig_false_receiver)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    trxid = contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

    print('----------------------------------')
    print('GAS USED test_close_by_sender', get_gas_used(chain, trxid))
    print('----------------------------------')


def test_close_by_sender_challenge_settle_by_receiver(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    trxid1 = contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    trxid2 = contract.transact({'from': receiver}).close(receiver, open_block_number, balance, balance_msg_sig)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

    print('----------------------------------')
    print('GAS USED test_close_by_sender_challenge_settle_by_receiver', get_gas_used(chain, trxid1) + get_gas_used(chain, trxid2))
    print('----------------------------------')


def test_close_by_sender_challenge_settle_by_sender(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = current_deposit - 1

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    trxid1 = contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    web3.testing.mine(challenge_period + 1)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    trxid2 = contract.transact({'from': sender}).settle(receiver, open_block_number)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

    print('----------------------------------')
    print('GAS USED test_close_by_sender_challenge_settle_by_sender', get_gas_used(chain, trxid1) + get_gas_used(chain, trxid2))
    print('----------------------------------')

def test_close_by_sender_challenge_settle_by_sender2(web3, chain, contract, channel):
    (sender, receiver, open_block_number) = channel
    (A) = web3.eth.accounts[3]

    current_deposit = get_current_deposit(contract, channel)
    balance = 0

    balance_msg = get_balance_message(receiver, open_block_number, balance)
    balance_msg_sig, addr = sign.check(balance_msg, tester.k1)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(contract.address)

    channel_pre_close_tests(contract, channel)
    trxid1 = contract.transact({'from': sender}).close(receiver, open_block_number, balance, balance_msg_sig)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).settle(receiver, open_block_number)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    web3.testing.mine(challenge_period + 1)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': receiver}).settle(receiver, open_block_number)

    trxid2 = contract.transact({'from': sender}).settle(receiver, open_block_number)

    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (current_deposit - balance)
    contract_post_balance = contract_pre_balance - current_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(contract.address) == contract_post_balance

    channel_settle_tests(contract, channel)

    print('----------------------------------')
    print('GAS USED test_close_by_sender_challenge_settle_by_sender2', get_gas_used(chain, trxid1) + get_gas_used(chain, trxid2))
    print('----------------------------------')


def test_channel_20_create(web3, chain, contract):
    (Owner, A, B, C, D) = web3.eth.accounts[:5]
    depozit_B = 100
    depozit_D = 120

    gas_used_create = 0

    # Fund accounts with tokens
    token.transact({"from": Owner}).transfer(B, depozit_B)
    token.transact({"from": Owner}).transfer(D, depozit_D)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({"from": B}).createChannelERC20(A, depozit_B)

    # Approve token allowance
    trxid = token.transact({"from": B}).approve(contract.address, depozit_B)
    gas_used_create += get_gas_used(chain, trxid)

    with pytest.raises(TypeError):
        contract.transact({"from": B}).createChannelERC20(A, -2)

    # Cannot create a channel if tokens were not approved
    with pytest.raises(tester.TransactionFailed):
        contract.transact({"from": D}).createChannelERC20(C, depozit_D)

    assert token.call().balanceOf(contract.address) == 0
    pre_balance_B = token.call().balanceOf(B)

    # Create channel
    trxid = contract.transact({"from": B}).createChannelERC20(A, depozit_B)
    gas_used_create += get_gas_used(chain, trxid)

    # Check balances
    assert token.call().balanceOf(contract.address) == depozit_B
    assert token.call().allowance(B, contract.address) == 0
    assert token.call().balanceOf(B) == pre_balance_B - depozit_B

    open_block_number = get_last_open_block_number(contract)

    channel_data = contract.call().getChannelInfo(B, A, open_block_number)
    print('-- --- -- channel_data', channel_data)
    assert channel_data[1] == 100  # deposit
    assert channel_data[2] == 0  # settle_block_number
    assert channel_data[3] == 0  # closing_balance

    print('----------------------------------')
    print('GAS USED test_channel_20_create', gas_used_create)
    print('----------------------------------')


def test_channel_topup_20(web3, chain, contract, channel_20):
    (sender, receiver, open_block_number) = channel_20
    (A) = web3.eth.accounts[3]
    top_up_deposit = 14

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUpERC20(receiver, open_block_number, top_up_deposit)

    # Approve token allowance
    trxid = token.transact({"from": sender}).approve(contract.address, top_up_deposit)
    gas_used_approve = get_gas_used(chain, trxid)

    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': A}).topUpERC20(receiver, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUpERC20(A, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUpERC20(receiver, open_block_number, 0)
    with pytest.raises(tester.TransactionFailed):
        contract.transact({'from': sender}).topUpERC20(receiver, 0, top_up_deposit)

    trxid = contract.transact({'from': sender}).topUpERC20(receiver, open_block_number, top_up_deposit)

    channel_data = contract.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print('----------------------------------')
    print('GAS USED test_channel_topup_20', gas_used_approve + get_gas_used(chain, trxid))
    print('----------------------------------')

def test_last_test_event_timeout():
    with Timeout(20) as timeout:
        timeout.sleep(2)

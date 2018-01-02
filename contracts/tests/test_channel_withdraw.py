import pytest
from ethereum import tester
from utils import sign
from tests.utils import balance_proof_hash, closing_message_hash
from tests.fixtures import (
    contract_params,
    channel_params,
    owner_index,
    owner,
    create_accounts,
    get_accounts,
    create_contract,
    get_token_contract,
    txn_gas,
    print_gas,
    get_block,
    event_handler,
    fake_address,
    MAX_UINT256,
    MAX_UINT32,
    MAX_UINT192,
    uraiden_events
)
from tests.fixtures_uraiden import (
    token_contract,
    token_instance,
    get_uraiden_contract,
    uraiden_contract,
    uraiden_instance,
    get_channel,
    checkWithdrawEvent
)


def test_withdraw_call(channel_params, uraiden_instance, get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    withdraw_balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": receiver}).withdraw(
            -2,
            withdraw_balance,
            balance_msg_sig
        )
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": receiver}).withdraw(
            MAX_UINT32 + 1,
            withdraw_balance,
            balance_msg_sig
        )
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            -1,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            withdraw_balance,
            bytearray()
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            0,
            balance_msg_sig
        )

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance,
        balance_msg_sig
    )


def test_withdraw_fail_no_channel(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel):
    A = get_accounts(1, 5)[0]
    (sender, receiver, open_block_number) = get_channel()[:3]
    withdraw_balance = 10

    balance_message_hash_A = balance_proof_hash(
        A,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig_A, addr = sign.check(balance_message_hash_A, tester.k5)
    assert addr == A

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).withdraw(
            open_block_number,
            withdraw_balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": A}).withdraw(
            open_block_number,
            withdraw_balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            withdraw_balance,
            balance_msg_sig_A
        )


def test_withdraw_balance(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    withdraw_balance_ok = channel_params['deposit']
    withdraw_balance_big = channel_params['deposit'] + 1

    balance_message_hash_big = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance_big,
        uraiden_instance.address
    )
    balance_msg_sig_big, addr = sign.check(balance_message_hash_big, tester.k2)
    assert addr == sender

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance_ok,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            withdraw_balance_big,
            balance_msg_sig_big
        )

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance_ok,
        balance_msg_sig
    )


def test_withdraw_fail_in_challenge_period(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    withdraw_balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    # Should fail if the channel is already in a challenge period
    uraiden_instance.transact({"from": sender}).uncooperativeClose(
        receiver,
        open_block_number,
        withdraw_balance
    )

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_info[2] > 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            withdraw_balance,
            balance_msg_sig
        )


def test_withdraw_topup(owner, uraiden_instance, token_instance, get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    deposit = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)[1]
    withdraw_balance = deposit

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance,
        balance_msg_sig
    )

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    deposit -= withdraw_balance
    assert channel_info[1] == deposit

    # Make sure we can top up the channel after withdrawal
    top_up_deposit = 300
    top_up_data = receiver[2:].zfill(40) + hex(open_block_number)[2:].zfill(8)
    top_up_data = bytes.fromhex(top_up_data)

    # Fund accounts with tokens
    token_instance.transact({"from": owner}).transfer(sender, top_up_deposit)

    # Top up channel
    token_instance.transact({"from": sender}).transfer(uraiden_instance.address, top_up_deposit, top_up_data)

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    deposit += top_up_deposit
    assert channel_info[1] == deposit


def test_withdraw_state(
        contract_params,
        channel_params,
        uraiden_instance,
        token_instance,
        get_channel,
        get_block,
        print_gas):
    (sender, receiver, open_block_number) = get_channel()[:3]
    deposit = channel_params['deposit']
    withdraw_balance1 = 20
    withdraw_balance2 = deposit - 20

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance1,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    # Memorize balances for tests
    uraiden_pre_balance = token_instance.call().balanceOf(uraiden_instance.address)
    sender_pre_balance = token_instance.call().balanceOf(sender)
    receiver_pre_balance = token_instance.call().balanceOf(receiver)

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance1,
        balance_msg_sig
    )

    # Check channel info
    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    # deposit
    assert channel_info[1] == deposit - withdraw_balance1
    assert channel_info[2] == 0
    assert channel_info[3] == 0

    # Check token balances post withrawal
    uraiden_balance = uraiden_pre_balance - withdraw_balance1
    assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_balance
    assert token_instance.call().balanceOf(sender) == sender_pre_balance
    assert token_instance.call().balanceOf(receiver) == receiver_pre_balance + withdraw_balance1

    print_gas(txn_hash, 'withdraw')

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance2,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance2,
        balance_msg_sig
    )

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    # deposit
    assert channel_info[1] == 0
    assert channel_info[2] == 0
    assert channel_info[3] == 0

    # Check token balances post withrawal
    uraiden_balance = uraiden_pre_balance - deposit
    assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_balance
    assert token_instance.call().balanceOf(sender) == sender_pre_balance
    assert token_instance.call().balanceOf(receiver) == receiver_pre_balance + deposit

    print_gas(txn_hash, 'withdraw')


def test_withdraw_event(
        channel_params,
        uraiden_instance,
        get_channel,
        event_handler):
    (sender, receiver, open_block_number) = get_channel()[:3]
    ev_handler = event_handler(uraiden_instance)
    withdraw_balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        withdraw_balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert addr == sender

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        withdraw_balance,
        balance_msg_sig
    )

    ev_handler.add(txn_hash, uraiden_events['withdraw'], checkWithdrawEvent(
        sender,
        receiver,
        open_block_number,
        withdraw_balance)
    )
    ev_handler.check()

import pytest
from ethereum import tester
from eth_utils import encode_hex, is_same_address
from utils import sign
from tests.utils import balance_proof_hash, closing_message_hash
from tests.constants import (
    MAX_UINT32,
    URAIDEN_EVENTS,
)
from tests.utils import (
    checkWithdrawEvent,
)


def test_withdraw_call(channel_params, uraiden_instance, get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": receiver}).withdraw(
            -2,
            balance,
            balance_msg_sig
        )
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": receiver}).withdraw(
            MAX_UINT32 + 1,
            balance,
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
            balance,
            encode_hex(bytearray())
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            0,
            balance_msg_sig
        )

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance,
        balance_msg_sig
    )


def test_withdraw_fail_no_channel(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel):
    A = get_accounts(1, 5)[0]
    (sender, receiver, open_block_number) = get_channel()[:3]
    balance = 10

    balance_message_hash_A = balance_proof_hash(
        A,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig_A, addr = sign.check(balance_message_hash_A, tester.k5)
    assert is_same_address(addr, A)

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).withdraw(
            open_block_number,
            balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": A}).withdraw(
            open_block_number,
            balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            balance,
            balance_msg_sig_A
        )


def test_balance_big(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel):
    (sender, receiver, open_block_number) = get_channel()[:3]
    balance_ok = channel_params['deposit']
    balance_big = channel_params['deposit'] + 1

    balance_message_hash_big = balance_proof_hash(
        receiver,
        open_block_number,
        balance_big,
        uraiden_instance.address
    )
    balance_msg_sig_big, addr = sign.check(balance_message_hash_big, tester.k2)
    assert is_same_address(addr, sender)

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance_ok,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            balance_big,
            balance_msg_sig_big
        )

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance_ok,
        balance_msg_sig
    )


def test_balance_remaining_big(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel
):
    (sender, receiver, open_block_number) = get_channel()[:3]
    balance1 = 30
    balance2_big = channel_params['deposit'] + 1
    balance2_ok = channel_params['deposit']

    balance_message_hash1 = balance_proof_hash(
        receiver,
        open_block_number,
        balance1,
        uraiden_instance.address
    )
    balance_msg_sig1, addr = sign.check(balance_message_hash1, tester.k2)
    assert is_same_address(addr, sender)

    balance_message_hash2_big = balance_proof_hash(
        receiver,
        open_block_number,
        balance2_big,
        uraiden_instance.address
    )
    balance_msg_sig2_big, addr = sign.check(balance_message_hash2_big, tester.k2)
    assert is_same_address(addr, sender)

    balance_message_hash2_ok = balance_proof_hash(
        receiver,
        open_block_number,
        balance2_ok,
        uraiden_instance.address
    )
    balance_msg_sig2_ok, addr = sign.check(balance_message_hash2_ok, tester.k2)
    assert is_same_address(addr, sender)

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance1,
        balance_msg_sig1
    )

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            balance2_big,
            balance_msg_sig2_big
        )

    uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance2_ok,
        balance_msg_sig2_ok
    )


def test_withdraw_fail_in_challenge_period(
        channel_params,
        get_accounts,
        uraiden_instance,
        get_channel
):
    (sender, receiver, open_block_number) = get_channel()[:3]
    balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    # Should fail if the channel is already in a challenge period
    uraiden_instance.transact({"from": sender}).uncooperativeClose(
        receiver,
        open_block_number,
        balance
    )

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_info[2] > 0  # settle_block_number

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": receiver}).withdraw(
            open_block_number,
            balance,
            balance_msg_sig
        )


def test_withdraw_state(
        contract_params,
        channel_params,
        uraiden_instance,
        token_instance,
        get_channel,
        get_block,
        print_gas
):
    (sender, receiver, open_block_number) = get_channel()[:3]
    deposit = channel_params['deposit']
    balance1 = 20
    balance2 = deposit

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance1,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    # Memorize balances for tests
    uraiden_pre_balance = token_instance.call().balanceOf(uraiden_instance.address)
    sender_pre_balance = token_instance.call().balanceOf(sender)
    receiver_pre_balance = token_instance.call().balanceOf(receiver)

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance1,
        balance_msg_sig
    )

    # Check channel info
    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    # deposit
    assert channel_info[1] == deposit
    assert channel_info[2] == 0
    assert channel_info[3] == 0
    assert channel_info[4] == balance1

    # Check token balances post withrawal
    uraiden_balance = uraiden_pre_balance - balance1
    assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_balance
    assert token_instance.call().balanceOf(sender) == sender_pre_balance
    assert token_instance.call().balanceOf(receiver) == receiver_pre_balance + balance1

    print_gas(txn_hash, 'withdraw')

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance2,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance2,
        balance_msg_sig
    )

    channel_info = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    # deposit
    assert channel_info[1] == deposit
    assert channel_info[2] == 0
    assert channel_info[3] == 0
    assert channel_info[4] == balance2

    # Check token balances post withrawal
    uraiden_balance = uraiden_pre_balance - deposit
    assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_balance
    assert token_instance.call().balanceOf(sender) == sender_pre_balance
    assert token_instance.call().balanceOf(receiver) == receiver_pre_balance + deposit

    print_gas(txn_hash, 'withdraw')


def test_close_after_withdraw(
        contract_params,
        channel_params,
        uraiden_instance,
        token_instance,
        get_channel,
        get_block,
        print_gas
):
    (sender, receiver, open_block_number) = get_channel()[:3]
    deposit = channel_params['deposit']
    balance1 = 20
    balance2 = deposit

    balance_message_hash1 = balance_proof_hash(
        receiver,
        open_block_number,
        balance1,
        uraiden_instance.address
    )
    balance_msg_sig1, addr = sign.check(balance_message_hash1, tester.k2)
    assert is_same_address(addr, sender)

    # Withdraw some tokens
    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance1,
        balance_msg_sig1
    )
    assert txn_hash is not None

    # Cooperatively close the channel
    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance2,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    closing_msg_hash = closing_message_hash(
        sender,
        open_block_number,
        balance2,
        uraiden_instance.address
    )
    closing_sig, addr = sign.check(closing_msg_hash, tester.k3)

    # Memorize balances for tests
    uraiden_pre_balance = token_instance.call().balanceOf(uraiden_instance.address)
    sender_pre_balance = token_instance.call().balanceOf(sender)
    receiver_pre_balance = token_instance.call().balanceOf(receiver)

    uraiden_instance.transact({"from": receiver}).cooperativeClose(
        receiver,
        open_block_number,
        balance2,
        balance_msg_sig,
        closing_sig
    )

    # Check post closing balances
    receiver_post_balance = receiver_pre_balance + (balance2 - balance1)
    sender_post_balance = sender_pre_balance + (deposit - balance2)
    uraiden_post_balance = uraiden_pre_balance - (balance2 - balance1)

    assert token_instance.call().balanceOf(receiver) == receiver_post_balance
    assert token_instance.call().balanceOf(sender) == sender_post_balance
    assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_post_balance


def test_withdraw_event(
        channel_params,
        uraiden_instance,
        get_channel,
        event_handler):
    (sender, receiver, open_block_number) = get_channel()[:3]
    ev_handler = event_handler(uraiden_instance)
    balance = 30

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    assert is_same_address(addr, sender)

    txn_hash = uraiden_instance.transact({"from": receiver}).withdraw(
        open_block_number,
        balance,
        balance_msg_sig
    )

    ev_handler.add(txn_hash, URAIDEN_EVENTS['withdraw'], checkWithdrawEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

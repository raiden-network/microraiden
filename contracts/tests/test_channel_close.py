import pytest
from ethereum import tester
from utils import sign
from tests.utils import balance_proof_hash
from utils.utils import sol_sha3
from tests.fixtures import (
    contract_params,
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
    MAX_UINT,
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
    channel_settle_tests,
    channel_pre_close_tests,
    checkClosedEvent,
    checkSettledEvent
)


def test_close_call(get_accounts, uraiden_instance, token_instance, get_channel):
    (sender, receiver, A) = get_accounts(3)
    channel_deposit = 450
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)
    (sender, receiver, open_block_number) = channel
    balance = channel_deposit - 10

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)

    # Cannot close what was not opened
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).uncooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).uncooperativeClose(
            A,
            open_block_number,
            balance,
            balance_msg_sig
        )

    # Cannot close if arguments not correct
    with pytest.raises(ValueError):
        uraiden_instance.transact({'from': sender}).initChallengePeriod(
            receiver,
            open_block_number,
            balance
        )
    with pytest.raises(ValueError):
        uraiden_instance.transact({'from': receiver}).settleChannel(
            sender,
            receiver,
            open_block_number,
            balance
        )


def test_close_by_receiver(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    print_gas,
    event_handler):
    token = token_instance
    (sender, receiver, A) = get_accounts(3)
    ev_handler = event_handler(uraiden_instance)
    channel_deposit = 800
    top_up_deposit = 14

    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)
    (sender, receiver, open_block_number) = channel

    channel_pre_close_tests(uraiden_instance, token_instance, channel, top_up_deposit)

    balance = channel_deposit - 1

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    balance_msg_sig_false, addr2 = sign.check(balance_message_hash, tester.k4)
    assert addr == sender

    contract_verified_address = uraiden_instance.call().verifyBalanceProof(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )
    assert contract_verified_address == sender

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).uncooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).uncooperativeClose(
            receiver,
            open_block_number + 1,
            balance,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).uncooperativeClose(
            receiver,
            open_block_number,
            balance + 1,
            balance_msg_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).uncooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig_false
        )

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(uraiden_instance.address)

    txn_hash = uraiden_instance.transact({'from': receiver}).uncooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )

    channel_deposit += top_up_deposit
    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (channel_deposit - balance)
    contract_post_balance = contract_pre_balance - channel_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(uraiden_instance.address) == contract_post_balance

    channel_settle_tests(uraiden_instance, token_instance, channel)

    # TODO:
    # with pytest.raises(Exception):
    #    ev_handler.add(txn_hash, uraiden_events['closed'], checkClosedEvent(sender, receiver, open_block_number, balance))
    ev_handler.add(txn_hash, uraiden_events['settled'], checkSettledEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    print_gas(txn_hash, 'test_close_by_receiver')


def test_close_by_sender(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    print_gas,
    event_handler):
    token = token_instance
    (sender, receiver, A) = get_accounts(3)
    ev_handler = event_handler(uraiden_instance)
    channel_deposit = 800
    top_up_deposit = 14
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)
    (sender, receiver, open_block_number) = channel

    balance = channel_deposit - 1

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_message_hash_false_receiver = balance_proof_hash(
        A,
        open_block_number,
        balance,
        uraiden_instance.address
    )

    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)
    balance_msg_sig_false_signer, addr = sign.check(balance_message_hash, tester.k4)
    balance_msg_sig_false_receiver, addr = sign.check(balance_message_hash_false_receiver, tester.k4)

    closing_sig, addr = sign.check(sol_sha3(balance_msg_sig), tester.k3)
    closing_sig_false_signer, addr = sign.check(sol_sha3(balance_msg_sig), tester.k4)
    closing_sig_false_receiver, addr = sign.check(
        sol_sha3(balance_msg_sig_false_receiver),
        tester.k3
    )

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            A,
            open_block_number,
            balance,
            balance_msg_sig,
            closing_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number - 3,
            balance,
            balance_msg_sig,
            closing_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number,
            balance + 5,
            balance_msg_sig,
            closing_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig_false_signer,
            closing_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig_false_receiver,
            closing_sig
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig,
            closing_sig_false_signer
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).cooperativeClose(
            receiver,
            open_block_number,
            balance,
            balance_msg_sig,
            closing_sig_false_receiver
        )

    channel_pre_close_tests(uraiden_instance, token_instance, channel, top_up_deposit)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(uraiden_instance.address)

    txn_hash = uraiden_instance.transact({'from': sender}).cooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig,
        closing_sig
    )

    # TODO: raise Exception
    # ev_handler.add(txn_hash, uraiden_events['closed'], checkClosedEvent(sender, receiver, open_block_number, balance))
    # ev_handler.check()

    channel_deposit += top_up_deposit
    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (channel_deposit - balance)
    contract_post_balance = contract_pre_balance - channel_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(uraiden_instance.address) == contract_post_balance

    channel_settle_tests(uraiden_instance, token_instance, channel)

    ev_handler.add(
        txn_hash,
        uraiden_events['settled'],
        checkSettledEvent(sender, receiver, open_block_number, balance)
    )
    ev_handler.check()

    print_gas(txn_hash, 'test_close_by_sender')


def test_close_by_sender_challenge_settle_by_receiver(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    print_gas,
    txn_gas,
    event_handler):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    channel_deposit = 800
    top_up_deposit = 14
    channel = get_channel(uraiden_instance, token_instance, channel_deposit)
    (sender, receiver, open_block_number) = channel

    balance = channel_deposit - 1

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)

    channel_pre_close_tests(uraiden_instance, token_instance, channel, top_up_deposit)
    txn_hash1 = uraiden_instance.transact({'from': sender}).uncooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    ev_handler.add(txn_hash1, uraiden_events['closed'], checkClosedEvent(sender, receiver, open_block_number, balance))
    ev_handler.check()

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(uraiden_instance.address)

    txn_hash2 = uraiden_instance.transact({'from': receiver}).uncooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )

    channel_deposit += top_up_deposit
    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (channel_deposit - balance)
    contract_post_balance = contract_pre_balance - channel_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(uraiden_instance.address) == contract_post_balance

    channel_settle_tests(uraiden_instance, token_instance, channel)

    ev_handler.add(txn_hash2, uraiden_events['settled'], checkSettledEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    print_gas(txn_hash1, 'test_close_by_sender_challenge_settle_by_receiver', txn_gas(txn_hash2))


def test_close_by_sender_challenge_settle_by_sender(
    web3,
    get_accounts,
    contract_params,
    uraiden_instance,
    token_instance,
    get_channel,
    print_gas,
    txn_gas,
    event_handler):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    channel_deposit = 800
    top_up_deposit = 14
    channel = get_channel(uraiden_instance, token_instance, channel_deposit)
    (sender, receiver, open_block_number) = channel

    balance = channel_deposit - 1

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)

    channel_pre_close_tests(uraiden_instance, token_instance, channel, top_up_deposit)

    txn_hash1 = uraiden_instance.transact({'from': sender}).uncooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    ev_handler.add(txn_hash1, uraiden_events['closed'], checkClosedEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).settle(receiver, open_block_number)

    web3.testing.mine(contract_params['challenge_period'] + 1)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).settle(receiver, open_block_number)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(uraiden_instance.address)

    txn_hash2 = uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    channel_deposit += top_up_deposit
    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (channel_deposit - balance)
    contract_post_balance = contract_pre_balance - channel_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(uraiden_instance.address) == contract_post_balance

    channel_settle_tests(uraiden_instance, token_instance, channel)

    ev_handler.add(txn_hash2, uraiden_events['settled'], checkSettledEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    print_gas(txn_hash1, 'test_close_by_sender_challenge_settle_by_sender', txn_gas(txn_hash2))


def test_close_by_sender_challenge_settle_by_sender2(
    web3,
    contract_params,
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    print_gas,
    txn_gas,
    event_handler):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    channel_deposit = 800
    top_up_deposit = 14
    channel = get_channel(uraiden_instance, token_instance, channel_deposit)
    (sender, receiver, open_block_number) = channel

    balance = 0

    balance_message_hash = balance_proof_hash(
        receiver,
        open_block_number,
        balance,
        uraiden_instance.address
    )
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)

    channel_pre_close_tests(uraiden_instance, token_instance, channel, top_up_deposit)

    txn_hash1 = uraiden_instance.transact({'from': sender}).uncooperativeClose(
        receiver,
        open_block_number,
        balance,
        balance_msg_sig
    )

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[2] != 0  # settle_block_number

    ev_handler.add(txn_hash1, uraiden_events['closed'], checkClosedEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).settle(receiver, open_block_number)

    web3.testing.mine(contract_params['challenge_period'] + 1)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': receiver}).settle(receiver, open_block_number)

    receiver_pre_balance = token.call().balanceOf(receiver)
    sender_pre_balance = token.call().balanceOf(sender)
    contract_pre_balance = token.call().balanceOf(uraiden_instance.address)

    txn_hash2 = uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    channel_deposit += top_up_deposit
    receiver_post_balance = receiver_pre_balance + balance
    sender_post_balance = sender_pre_balance + (channel_deposit - balance)
    contract_post_balance = contract_pre_balance - channel_deposit

    assert token.call().balanceOf(receiver) == receiver_post_balance
    assert token.call().balanceOf(sender) == sender_post_balance
    assert token.call().balanceOf(uraiden_instance.address) == contract_post_balance

    channel_settle_tests(uraiden_instance, token_instance, channel)

    ev_handler.add(txn_hash2, uraiden_events['settled'], checkSettledEvent(
        sender,
        receiver,
        open_block_number,
        balance)
    )
    ev_handler.check()

    print_gas(txn_hash1, 'test_close_by_sender_challenge_settle_by_sender2', txn_gas(txn_hash2))

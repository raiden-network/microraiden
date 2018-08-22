import pytest
from ethereum import tester
from tests.constants import (
    URAIDEN_EVENTS,
    CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT,
    FAKE_ADDRESS,
    MAX_UINT192,
)
from tests.utils import (
    checkToppedUpEvent,
)


def test_channel_topup_223(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    event_handler,
    print_gas
):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver, A, B) = get_accounts(4)
    channel_deposit = 700
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)[:3]
    (sender, receiver, open_block_number) = channel
    top_up_deposit = 14

    # address 20 bytes
    # padded block number from uint32 (4 bytes) to 32 bytes
    top_up_data = sender[2:] + receiver[2:] + hex(open_block_number)[2:].zfill(8)
    top_up_data = bytes.fromhex(top_up_data)

    top_up_data_wrong_receiver = sender[2:].zfill(64) + hex(open_block_number)[2:].zfill(8)

    top_up_data_wrong_block = receiver[2:].zfill(64) + hex(open_block_number + 30)[2:].zfill(8)

    with pytest.raises(tester.TransactionFailed):
        token.transact(
            {"from": sender}
        ).transfer(uraiden_instance.address, top_up_deposit, top_up_data_wrong_receiver)
    with pytest.raises(tester.TransactionFailed):
        token.transact(
            {"from": sender}
        ).transfer(uraiden_instance.address, top_up_deposit, top_up_data_wrong_block)
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(uraiden_instance.address, 0, top_up_data)

    # Call Token - this calls uraiden_instance.tokenFallback
    txn_hash = token.transact(
        {"from": sender}
    ).transfer(uraiden_instance.address, top_up_deposit, top_up_data)

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print_gas(txn_hash, 'test_channel_topup_223')

    # Check topup event
    ev_handler.add(
        txn_hash,
        URAIDEN_EVENTS['topup'],
        checkToppedUpEvent(
            sender,
            receiver,
            open_block_number,
            top_up_deposit,
            channel_deposit + top_up_deposit
        )
    )
    ev_handler.check()


def test_channel_topup_223_bounty_limit(
    get_accounts,
    owner,
    uraiden_instance,
    token_instance,
    get_channel
):
    token = token_instance
    (sender, receiver, A) = get_accounts(3)
    channel_deposit = 1
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)[:3]
    (sender, receiver, open_block_number) = channel

    top_up_data = sender[2:] + receiver[2:] + hex(open_block_number)[2:].zfill(8)
    top_up_data = bytes.fromhex(top_up_data)

    # See how many tokens we need to reach channel_deposit_bugbounty_limit
    added_deposit = CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT - channel_deposit

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, added_deposit + 1)

    pre_balance = token.call().balanceOf(uraiden_instance.address)

    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            added_deposit + 1,
            top_up_data
        )
    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            added_deposit + 20,
            top_up_data
        )

    token_instance.transact({"from": sender}).transfer(
        uraiden_instance.address,
        added_deposit,
        top_up_data
    )

    post_balance = pre_balance + added_deposit
    assert token_instance.call().balanceOf(uraiden_instance.address) == post_balance

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT


def test_channel_topup_20(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    txn_gas,
    event_handler,
    print_gas
):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver, A) = get_accounts(3)
    channel_deposit = 999
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)[:3]
    (sender, receiver, open_block_number) = channel
    top_up_deposit = 14

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(
            receiver,
            open_block_number,
            top_up_deposit
        )

    # Approve token allowance
    txn_hash = token.transact({"from": sender}).approve(uraiden_instance.address, top_up_deposit)
    gas_used_approve = txn_gas(txn_hash)

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUp(0x0, top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUp('0x0', top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUp(FAKE_ADDRESS, top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUp(receiver, -3)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUp(receiver, MAX_UINT192 + 1)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).topUp(receiver, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(A, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(receiver, open_block_number, 0)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(receiver, 0, top_up_deposit)

    txn_hash = uraiden_instance.transact({'from': sender}).topUp(
        receiver,
        open_block_number,
        top_up_deposit
    )

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print_gas(txn_hash, 'test_channel_topup_20', gas_used_approve)

    # Check topup event
    ev_handler.add(txn_hash, URAIDEN_EVENTS['topup'], checkToppedUpEvent(
        sender,
        receiver,
        open_block_number,
        top_up_deposit,
        channel_deposit + top_up_deposit)
    )
    ev_handler.check()


def test_channel_topup_20_bounty_limit(
    get_accounts,
    owner,
    uraiden_instance,
    token_instance,
    get_channel
):
    token = token_instance
    (sender, receiver, A) = get_accounts(3)
    channel_deposit = 1
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)[:3]
    (sender, receiver, open_block_number) = channel

    # See how many tokens we need to reach channel_deposit_bugbounty_limit
    added_deposit = CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT - channel_deposit

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, added_deposit + 1)

    # Approve token allowance
    txn_hash = token.transact(
        {"from": sender}
    ).approve(uraiden_instance.address, added_deposit + 1)
    assert txn_hash is not None

    pre_balance = token.call().balanceOf(uraiden_instance.address)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(
            receiver,
            open_block_number,
            added_deposit + 1
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(
            receiver,
            open_block_number,
            added_deposit + 50
        )

    uraiden_instance.transact({'from': sender}).topUp(
        receiver,
        open_block_number,
        added_deposit
    )

    post_balance = pre_balance + added_deposit
    assert token_instance.call().balanceOf(uraiden_instance.address) == post_balance

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT


def test_topup_token_fallback_uint_conversion(
    contract_params,
    owner,
    get_accounts,
    uraiden_instance,
    token_instance,
    get_block
):
    token = token_instance
    (sender, receiver) = get_accounts(2)

    # Make sure you have a fixture with a supply > 2 ** 192
    supply = contract_params['supply']
    deposit = 100
    top_up_deposit = supply - 100

    txdata = bytes.fromhex(sender[2:] + receiver[2:])

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, supply)
    assert token.call().balanceOf(sender) == supply

    # Open a channel with tokenFallback
    txn_hash = token_instance.transact(
        {"from": sender}
    ).transfer(uraiden_instance.address, deposit, txdata)
    open_block_number = get_block(txn_hash)

    assert token.call().balanceOf(uraiden_instance.address) == deposit
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == deposit

    top_up_data = sender[2:] + receiver[2:] + hex(open_block_number)[2:].zfill(8)
    top_up_data = bytes.fromhex(top_up_data)

    # TopUp a channel with tokenFallback
    if deposit > 2 ** 192:
        with pytest.raises(tester.TransactionFailed):
            txn_hash = token_instance.transact({"from": sender}).transfer(
                uraiden_instance.address,
                top_up_deposit,
                top_up_data
            )

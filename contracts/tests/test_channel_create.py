import pytest
from ethereum import tester
from tests.fixtures import (
    channel_deposit_bugbounty_limit,
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
    empty_address,
    MAX_UINT256,
    MAX_UINT192,
    uraiden_events
)
from tests.fixtures_uraiden import (
    token_contract,
    token_instance,
    get_uraiden_contract,
    uraiden_contract,
    uraiden_instance,
    delegate_contract,
    delegate_instance,
    checkCreatedEvent
)


def test_channel_erc223_create(owner, get_accounts, uraiden_instance, token_instance):
    token = token_instance
    (sender, receiver, C, D) = get_accounts(4)
    deposit = 1000
    txdata = bytes.fromhex(sender[2:] + receiver[2:])
    txdata_fake = txdata[1:]

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)
    token.transact({"from": owner}).transfer(receiver, 20)

    with pytest.raises(TypeError):
        token_instance.transact({"from": sender}).transfer(0x0, deposit, txdata)
    with pytest.raises(TypeError):
        token_instance.transact({"from": sender}).transfer(fake_address, deposit, txdata)
    with pytest.raises(TypeError):
        token_instance.transact({"from": sender}).transfer(uraiden_instance.address, -2, txdata)
    with pytest.raises(TypeError):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            MAX_UINT256 + 1,
            txdata
        )
    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(empty_address, deposit, txdata)
    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            deposit,
            bytearray(10)
        )
    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            deposit,
            txdata_fake
        )

    # tokenFallback only callable by token
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': C}).tokenFallback(sender, 10, txdata)

    assert token_instance.call().balanceOf(uraiden_instance.address) == 0

    # Deposit 0 is possible now
    token_instance.transact({"from": sender}).transfer(uraiden_instance.address, 0, txdata)

    token_instance.transact({"from": sender}).transfer(uraiden_instance.address, deposit, txdata)


def test_channel_erc223_create_bounty_limit(
        get_block,
        owner,
        get_accounts,
        uraiden_instance,
        token_instance):
    token = token_instance
    (sender, receiver, C, D) = get_accounts(4)
    txdata = bytes.fromhex(sender[2:] + receiver[2:])

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, channel_deposit_bugbounty_limit + 1)

    pre_balance = token_instance.call().balanceOf(uraiden_instance.address)

    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            channel_deposit_bugbounty_limit + 1,
            txdata
        )
    with pytest.raises(tester.TransactionFailed):
        token_instance.transact({"from": sender}).transfer(
            uraiden_instance.address,
            channel_deposit_bugbounty_limit + 10,
            txdata
        )

    txn_hash = token_instance.transact({"from": sender}).transfer(
        uraiden_instance.address,
        channel_deposit_bugbounty_limit,
        txdata
    )

    post_balance = pre_balance + channel_deposit_bugbounty_limit
    assert token_instance.call().balanceOf(uraiden_instance.address) == post_balance
    open_block_number = get_block(txn_hash)

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit_bugbounty_limit


def test_create_token_fallback_uint_conversion(
        owner,
        get_accounts,
        uraiden_contract,
        get_token_contract):
    token = get_token_contract([MAX_UINT192 + 100, 'CustomToken', 'TKN', 18])
    uraiden = uraiden_contract(token)
    (sender, receiver) = get_accounts(2)
    txdata = bytes.fromhex(sender[2:] + receiver[2:])

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, MAX_UINT192 + 5)
    assert token.call().balanceOf(sender) == MAX_UINT192 + 5

    # Open a channel with tokenFallback
    # uint192 deposit = uint192(_deposit), where _deposit is uint256
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(
            uraiden.address,
            MAX_UINT192 + 1,
            txdata
        )
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(
            uraiden.address,
            MAX_UINT192 + 4,
            txdata
        )

    # TODO - uncomment this after channel_deposit_bugbounty_limit is removed
    # txn_hash = token.transact({"from": sender}).transfer(
    #     uraiden.address,
    #     MAX_UINT192,
    #     txdata
    # )


def test_channel_erc223_event(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        event_handler,
        print_gas):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver) = get_accounts(2)
    deposit = 1000
    txdata = bytes.fromhex(sender[2:] + receiver[2:])

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)

    txn_hash = token_instance.transact({"from": sender}).transfer(
        uraiden_instance.address,
        1000,
        txdata
    )

    # Check creation event
    ev_handler.add(
        txn_hash,
        uraiden_events['created'],
        checkCreatedEvent(sender, receiver, deposit)
    )
    ev_handler.check()

    print_gas(txn_hash, 'channel_223_create')


def test_channel_erc20_create(owner, get_accounts, uraiden_instance, token_instance):
    token = token_instance
    (sender, receiver) = get_accounts(2)
    deposit = 1000

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)
    token.transact({"from": owner}).transfer(receiver, 20)

    # Cannot create a channel if tokens were not approved
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).createChannel(receiver, deposit)

    assert token_instance.call().balanceOf(uraiden_instance.address) == 0

    # Can create a channel with deposit 0
    uraiden_instance.transact({"from": sender}).createChannel(receiver, 0)

    # Approve token allowance
    token_instance.transact({"from": sender}).approve(uraiden_instance.address, deposit)

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannel(0x0, deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannel('0x0', deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannel(fake_address, deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannel(receiver, -3)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannel(receiver, MAX_UINT192 + 1)

    # Create channel
    uraiden_instance.transact({"from": sender}).createChannel(receiver, deposit)


def test_channel_erc20_create_bounty_limit(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        get_block):
    token = token_instance
    (sender, receiver) = get_accounts(2)

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, channel_deposit_bugbounty_limit + 1)

    # Approve token allowance
    token_instance.transact({"from": sender}).approve(
        uraiden_instance.address,
        channel_deposit_bugbounty_limit + 1
    )

    pre_balance = token_instance.call().balanceOf(uraiden_instance.address)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).createChannel(
            receiver,
            channel_deposit_bugbounty_limit + 1
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).createChannel(
            receiver,
            channel_deposit_bugbounty_limit + 100
        )

    txn_hash = uraiden_instance.transact({"from": sender}).createChannel(
        receiver,
        channel_deposit_bugbounty_limit
    )

    post_balance = pre_balance + channel_deposit_bugbounty_limit
    assert token_instance.call().balanceOf(uraiden_instance.address) == post_balance
    open_block_number = get_block(txn_hash)

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit_bugbounty_limit


def test_channel_erc20_event(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        event_handler,
        txn_gas,
        print_gas):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver) = get_accounts(2)
    deposit = 1000
    gas_used = 0

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)

    # Approve token allowance
    txn_hash_approve = token_instance.transact({"from": sender}).approve(uraiden_instance.address, deposit)
    gas_used += txn_gas(txn_hash_approve)

    # Create channel
    txn_hash = uraiden_instance.transact({"from": sender}).createChannel(receiver, deposit)

    # Check creation event
    ev_handler.add(
        txn_hash,
        uraiden_events['created'],
        checkCreatedEvent(sender, receiver, deposit)
    )
    ev_handler.check()

    print_gas(txn_hash, 'channel_20_create', gas_used)


def test_channel_create_state(
        owner,
        channel_params,
        get_accounts,
        uraiden_instance,
        token_instance,
        get_block):
    token = token_instance
    uraiden = uraiden_instance
    (sender, receiver) = get_accounts(2)
    deposit = channel_params['deposit']
    contract_type = channel_params['type']

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)
    token.transact({"from": owner}).transfer(receiver, 20)

    # Memorize balances for tests
    uraiden_pre_balance = token.call().balanceOf(uraiden.address)
    sender_pre_balance = token.call().balanceOf(sender)
    receiver_pre_balance = token.call().balanceOf(receiver)

    if contract_type == '20':
        token.transact({"from": sender}).approve(
            uraiden.address,
            deposit
        )
        txn_hash = uraiden.transact({"from": sender}).createChannel(
            receiver,
            deposit
        )
    else:
        txdata = bytes.fromhex(sender[2:] + receiver[2:])
        txn_hash = token.transact({"from": sender}).transfer(
            uraiden.address,
            deposit,
            txdata
        )

    # Check token balances post channel creation
    uraiden_balance = uraiden_pre_balance + deposit
    assert token.call().balanceOf(uraiden.address) == uraiden_balance
    assert token.call().balanceOf(sender) == sender_pre_balance - deposit
    assert token.call().balanceOf(receiver) == receiver_pre_balance

    open_block_number = get_block(txn_hash)
    channel_data = uraiden.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[0] == uraiden.call().getKey(
        sender,
        receiver,
        open_block_number
    )
    assert channel_data[1] == deposit
    assert channel_data[2] == 0
    assert channel_data[3] == 0

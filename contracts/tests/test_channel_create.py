import pytest
from ethereum import tester
from tests.fixtures import (
    channel_deposit_bugbounty_limit,
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
    empty_address,
    MAX_UINT,
    MAX_UINT192
)
from tests.fixtures_uraiden import (
    token_contract,
    token_instance,
    get_uraiden_contract,
    uraiden_contract,
    uraiden_instance,
)


def test_channel_223_create(owner, get_accounts, uraiden_instance, token_instance):
    token = token_instance
    (sender, receiver, C, D) = get_accounts(4)
    deposit = 1000
    txdata = bytes.fromhex(receiver[2:].zfill(40))
    # txdata_D = bytes.fromhex(D[2:].zfill(40))
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
            MAX_UINT + 1,
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


def test_channel_223_create_bounty_limit(get_block, owner, get_accounts, uraiden_instance, token_instance):
    token = token_instance
    (sender, receiver, C, D) = get_accounts(4)
    txdata = bytes.fromhex(receiver[2:].zfill(40))

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


def test_channel_20_create(owner, get_accounts, uraiden_instance, token_instance):
    token = token_instance
    (sender, receiver) = get_accounts(2)
    deposit = 1000

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit + 100)
    token.transact({"from": owner}).transfer(receiver, 20)

    # Cannot create a channel if tokens were not approved
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, deposit)

    assert token_instance.call().balanceOf(uraiden_instance.address) == 0

    # Can create a channel with deposit 0
    uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, 0)

    # Approve token allowance
    token_instance.transact({"from": sender}).approve(uraiden_instance.address, deposit)

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannelERC20(0x0, deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannelERC20('0x0', deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannelERC20(fake_address, deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, -3)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, MAX_UINT192 + 1)

    # Create channel
    uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, deposit)


def test_channel_20_create_bounty_limit(owner, get_accounts, uraiden_instance, token_instance, get_block):
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
        uraiden_instance.transact({"from": sender}).createChannelERC20(
            receiver,
            channel_deposit_bugbounty_limit + 1
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({"from": sender}).createChannelERC20(
            receiver,
            channel_deposit_bugbounty_limit + 100
        )

    txn_hash = uraiden_instance.transact({"from": sender}).createChannelERC20(
        receiver,
        channel_deposit_bugbounty_limit
    )

    post_balance = pre_balance + channel_deposit_bugbounty_limit
    assert token_instance.call().balanceOf(uraiden_instance.address) == post_balance
    open_block_number = get_block(txn_hash)

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit_bugbounty_limit


def test_create_token_fallback_uint_conversion(
    contract_params,
    owner,
    get_accounts,
    uraiden_instance,
    token_instance):
    token = token_instance
    (sender, receiver) = get_accounts(2)

    # Make sure you have a fixture with a supply > 2 ** 192 + 100
    deposit = contract_params['supply'] - 100
    txdata = bytes.fromhex(receiver[2:].zfill(40))

    # Fund accounts with tokens
    token.transact({"from": owner}).transfer(sender, deposit)
    assert token.call().balanceOf(sender) == deposit

    # Open a channel with tokenFallback
    if deposit > 2 ** 192:
        with pytest.raises(tester.TransactionFailed):
            txn_hash = token_instance.transact({"from": sender}).transfer(
                uraiden_instance.address,
                deposit,
                txdata
            )

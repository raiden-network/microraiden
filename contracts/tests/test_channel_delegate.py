import pytest
from ethereum import tester


def test_channel_erc223_create_delegate(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        delegate_instance,
        get_block):
    (sender, receiver) = get_accounts(2)
    deposit = 1000
    txdata = bytes.fromhex(sender[2:] + receiver[2:])

    # Delegate contract is a trusted contract
    assert uraiden_instance.call().trusted_contracts(delegate_instance.address)

    # Fund delegate contract with tokens
    token_instance.transact({"from": owner}).transfer(delegate_instance.address, deposit + 100)

    # Create channel through delegate
    txn_hash = delegate_instance.transact({"from": sender}).createChannelERC223(deposit, txdata)

    # Make sure the channel was created between sender and receiver
    open_block_number = get_block(txn_hash)
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[0] == uraiden_instance.call().getKey(
        sender,
        receiver,
        open_block_number
    )
    assert channel_data[1] == deposit
    assert channel_data[2] == 0
    assert channel_data[3] == 0


def test_channel_erc20_create_delegate(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        delegate_instance,
        get_block):
    (sender, receiver) = get_accounts(2)
    deposit = 1000

    # Delegate contract is a trusted contract
    assert uraiden_instance.call().trusted_contracts(delegate_instance.address)

    # Fund delegate with tokens
    token_instance.transact({"from": owner}).transfer(delegate_instance.address, deposit + 100)

    # Create channel through delegate
    txn_hash = delegate_instance.transact(
        {"from": sender}
    ).createChannelERC20(sender, receiver, deposit)

    # Make sure the channel was created between sender and receiver
    open_block_number = get_block(txn_hash)
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[0] == uraiden_instance.call().getKey(
        sender,
        receiver,
        open_block_number
    )
    assert channel_data[1] == deposit
    assert channel_data[2] == 0
    assert channel_data[3] == 0


def test_channel_erc223_topup_delegate(
        owner,
        uraiden_instance,
        token_instance,
        delegate_instance,
        get_channel
):
    deposit = 1000
    deposit_topup = 200
    (sender, receiver, open_block_number) = get_channel(
        uraiden_instance,
        token_instance,
        deposit
    )[:3]
    txdata = sender[2:] + receiver[2:] + hex(open_block_number)[2:].zfill(8)
    txdata = bytes.fromhex(txdata)

    # Delegate contract is a trusted contract
    assert uraiden_instance.call().trusted_contracts(delegate_instance.address)

    # Fund delegate with tokens
    token_instance.transact(
        {"from": owner}
    ).transfer(delegate_instance.address, deposit_topup + 100)

    # Top up channel through delegate
    delegate_instance.transact({"from": sender}).topUpERC223(deposit_topup, txdata)

    # Check channel deposit
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == deposit + deposit_topup


def test_channel_erc20_topup_delegate(
        owner,
        uraiden_instance,
        token_instance,
        delegate_instance,
        get_channel
):
    deposit = 1000
    deposit_topup = 200
    (sender, receiver, open_block_number) = get_channel(
        uraiden_instance,
        token_instance,
        deposit
    )[:3]

    # Delegate contract is a trusted contract
    assert uraiden_instance.call().trusted_contracts(delegate_instance.address)

    # Fund delegate with tokens
    token_instance.transact({"from": owner}).transfer(delegate_instance.address, deposit_topup)

    # Top up channel through delegate
    delegate_instance.transact({"from": sender}).topUpERC20(
        sender,
        receiver,
        open_block_number,
        deposit_topup
    )

    # Check channel deposit
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == deposit + deposit_topup


def test_delegate_remove_trusted_contract(
        owner,
        get_accounts,
        uraiden_instance,
        token_instance,
        delegate_instance):
    (sender, receiver) = get_accounts(2)
    deposit = 1000

    # Fund delegate with tokens
    token_instance.transact({"from": owner}).transfer(delegate_instance.address, deposit * 3)

    # Create channel through delegate
    delegate_instance.transact({"from": sender}).createChannelERC20(sender, receiver, deposit)

    # Remove trusted contract
    uraiden_instance.transact({"from": owner}).removeTrustedContracts([
        delegate_instance.address
    ])

    # Delegate create channel should fail now
    with pytest.raises(tester.TransactionFailed):
        delegate_instance.transact({"from": sender}).createChannelERC20(sender, receiver, deposit)

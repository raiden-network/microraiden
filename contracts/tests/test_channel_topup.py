import pytest
from ethereum import tester
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
    eip712_contract,
    eip712_instance,
    get_channel
)
from tests.fixtures_uraiden import checkToppedUpEvent


def test_channel_topup_223(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    event_handler,
    print_gas):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver, A, B) = get_accounts(4)
    channel_deposit = 700
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)
    (sender, receiver, open_block_number) = channel
    top_up_deposit = 14

    # address 20 bytes
    # padded block number from uint32 (4 bytes) to 32 bytes
    top_up_data = receiver[2:].zfill(40) + hex(open_block_number)[2:].zfill(8)
    top_up_data = bytes.fromhex(top_up_data)

    top_up_data_wrong_receiver = sender[2:].zfill(64) + hex(open_block_number)[2:].zfill(8)

    top_up_data_wrong_block = receiver[2:].zfill(64) + hex(open_block_number+30)[2:].zfill(8)

    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(uraiden_instance.address, top_up_deposit, top_up_data_wrong_receiver)
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(uraiden_instance.address, top_up_deposit, top_up_data_wrong_block)
    with pytest.raises(tester.TransactionFailed):
        token.transact({"from": sender}).transfer(uraiden_instance.address, 0, top_up_data)

    # Call Token - this calls uraiden_instance.tokenFallback
    txn_hash = token.transact({"from": sender}).transfer(uraiden_instance.address, top_up_deposit, top_up_data)

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print_gas(txn_hash, 'test_channel_topup_223')

    # Check topup event
    ev_handler.add(txn_hash, uraiden_events['topup'], checkToppedUpEvent(sender, receiver, open_block_number, top_up_deposit, channel_deposit + top_up_deposit))
    ev_handler.check()

    # TODO Test deposit > uint192
    '''
    channel = get_channel(uraiden_instance, token_instance, 100, A, B)
    (sender, receiver, open_block_number) = channel

    txn_hash = token.transact({"from": sender}).transfer(uraiden_instance.address, MAX_UINT192 - 100, top_up_data)
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == MAX_UINT192 - 100'''


def test_channel_topup_20(
    get_accounts,
    uraiden_instance,
    token_instance,
    get_channel,
    txn_gas,
    event_handler,
    print_gas):
    token = token_instance
    ev_handler = event_handler(uraiden_instance)
    (sender, receiver, A) = get_accounts(3)
    channel_deposit = 999
    channel = get_channel(uraiden_instance, token_instance, channel_deposit, sender, receiver)
    (sender, receiver, open_block_number) = channel
    top_up_deposit = 14

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUpERC20(
            receiver,
            open_block_number,
            top_up_deposit
        )

    # Approve token allowance
    txn_hash = token.transact({"from": sender}).approve(uraiden_instance.address, top_up_deposit)
    gas_used_approve = txn_gas(txn_hash)

    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUpERC20(0x0, top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUpERC20('0x0', top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUpERC20(fake_address, top_up_deposit)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUpERC20(receiver, -3)
    with pytest.raises(TypeError):
        uraiden_instance.transact({"from": sender}).topUpERC20(receiver, MAX_UINT192 + 1)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).topUpERC20(receiver, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUpERC20(A, open_block_number, top_up_deposit)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUpERC20(receiver, open_block_number, 0)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUpERC20(receiver, 0, top_up_deposit)

    txn_hash = uraiden_instance.transact({'from': sender}).topUpERC20(
        receiver,
        open_block_number,
        top_up_deposit
    )

    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[1] == channel_deposit + top_up_deposit  # deposit

    print_gas(txn_hash, 'test_channel_topup_20', gas_used_approve)

    # Check topup event
    ev_handler.add(txn_hash, uraiden_events['topup'], checkToppedUpEvent(
        sender,
        receiver,
        open_block_number,
        top_up_deposit,
        channel_deposit + top_up_deposit)
    )
    ev_handler.check()

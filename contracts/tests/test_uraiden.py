import pytest
import os
from ethereum import tester
from tests.fixtures import (
    uraiden_contract_version,
    contract_params,
    owner_index,
    owner,
    create_accounts,
    get_accounts,
    create_contract,
    get_token_contract,
    fake_address,
    empty_address,
    print_gas,
    txn_gas,
    get_block,
    MAX_UINT,
    MAX_UINT192
)
from tests.fixtures_uraiden import (
    token_contract,
    token_instance,
    get_uraiden_contract,
    uraiden_contract,
    uraiden_instance,
    eip712_contract,
    eip712_instance,
    get_channel,
    event_handler
)
# from tests.test_channel_create import get_channel


def test_uraiden_init(
    web3,
    owner,
    get_accounts,
    get_uraiden_contract,
    token_contract,
    uraiden_contract):
    token = token_contract()
    (A, B) = get_accounts(2)

    with pytest.raises(TypeError):
        get_uraiden_contract([token.address])
    with pytest.raises(TypeError):
        get_uraiden_contract([fake_address, 100])
    with pytest.raises(TypeError):
        get_uraiden_contract([token.address, -2])
    with pytest.raises(TypeError):
        get_uraiden_contract([token.address, 2 ** 32])
    with pytest.raises(TypeError):
        get_uraiden_contract([0x0, 100])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([empty_address, 100])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([A, 100])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([token.address, 0])

    uraiden = get_uraiden_contract([token.address, 2 ** 8 - 1])
    assert uraiden.call().owner_address() == owner
    assert uraiden.call().token()
    assert uraiden.call().challenge_period() == 2 ** 8 - 1
    assert token.call().balanceOf(uraiden.address) == 0
    assert web3.eth.getBalance(uraiden.address) == 0


def test_variable_access(owner, uraiden_contract, token_instance, contract_params):
    uraiden_instance = uraiden_contract()
    assert uraiden_instance.call().owner_address() == owner
    assert uraiden_instance.call().token()
    assert uraiden_instance.call().challenge_period() == contract_params['challenge_period']
    assert uraiden_instance.call().version() == uraiden_contract_version
    assert uraiden_instance.call().latest_version_address() == empty_address


def test_function_access(
    owner,
    get_accounts,
    uraiden_contract,
    uraiden_instance,
    token_instance,
    get_channel):
    (A, B, C, D) = get_accounts(4)
    uraiden_instance2 = uraiden_contract()
    channel = get_channel(uraiden_instance, token_instance, 100, A, B)
    (sender, receiver, open_block_number) = channel

    uraiden_instance.call().getKey(*channel)
    uraiden_instance.call().getChannelInfo(*channel)

    uraiden_instance.transact({'from': owner}).setLatestVersionAddress(uraiden_instance2.address)

    # even if TransactionFailed , this means the function is public / external
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().verifyBalanceProof(receiver, open_block_number, 10, bytearray(65))
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().tokenFallback(sender, 10, bytearray(20))
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': C}).createChannelERC20(D, 10)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().topUpERC20(receiver, open_block_number, 10)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().uncooperativeClose(receiver, open_block_number, 10, bytearray(65))
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().cooperativeClose(receiver, open_block_number, 10, bytearray(65), bytearray(65))
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().settle(receiver, open_block_number)

    # Test functions are private
    # raise ValueError("No matching functions found")
    with pytest.raises(ValueError):
        uraiden_instance.transact().createChannelPrivate(*channel)
    with pytest.raises(ValueError):
        uraiden_instance.transact().topUpPrivate(*channel, 10)
    with pytest.raises(ValueError):
        uraiden_instance.transact().initChallengePeriod(receiver, open_block_number, 10)
    with pytest.raises(ValueError):
        uraiden_instance.transact().settleChannel(*channel, 10)


def test_version(web3, owner, get_accounts, get_uraiden_contract, uraiden_instance, token_instance):
    (A, B) = get_accounts(2)
    token = token_instance
    other_contract = get_uraiden_contract([token.address, 10], {'from': A})

    assert uraiden_instance.call().version() == uraiden_contract_version
    assert uraiden_instance.call().latest_version_address() == empty_address

    with pytest.raises(TypeError):
        uraiden_instance.transact({'from': owner}).setLatestVersionAddress('0x0')
    with pytest.raises(TypeError):
        uraiden_instance.transact({'from': owner}).setLatestVersionAddress(123)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': owner}).setLatestVersionAddress(empty_address)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': owner}).setLatestVersionAddress(A)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).setLatestVersionAddress(other_contract.address)

    uraiden_instance.transact({'from': owner}).setLatestVersionAddress(other_contract.address)
    assert uraiden_instance.call().latest_version_address() == other_contract.address


def test_get_channel_info(web3, get_accounts, uraiden_instance, token_instance, get_channel):
    (A, B, C, D) = get_accounts(4)
    channel = get_channel(uraiden_instance, token_instance, 100, C, D)
    (sender, receiver, open_block_number) = channel

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number-2)
    web3.testing.mine(2)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.call().getChannelInfo(A, receiver, open_block_number)
    web3.testing.mine(2)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.call().getChannelInfo(sender, A, open_block_number)

    web3.testing.mine(2)
    channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
    assert channel_data[0] == uraiden_instance.call().getKey(sender, receiver, open_block_number)
    assert channel_data[1] == 100
    assert channel_data[2] == 0
    assert channel_data[3] == 0

import pytest
from ethereum import tester
from eth_utils import encode_hex, is_same_address
from tests.constants import (
    FAKE_ADDRESS,
    CHALLENGE_PERIOD_MIN,
    EMPTY_ADDRESS,
    URAIDEN_CONTRACT_VERSION,
    CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT,
)


def test_uraiden_init(
    web3,
    owner,
    get_accounts,
    get_uraiden_contract,
    token_contract,
    uraiden_contract
):
    token = token_contract()
    fake_token = uraiden_contract()
    (A, B) = get_accounts(2)

    with pytest.raises(TypeError):
        get_uraiden_contract([token.address])
    with pytest.raises(TypeError):
        get_uraiden_contract([token.address, 500])
    with pytest.raises(TypeError):
        get_uraiden_contract([FAKE_ADDRESS, CHALLENGE_PERIOD_MIN, []])
    with pytest.raises(TypeError):
        get_uraiden_contract([token.address, -2, []])
    with pytest.raises(TypeError):
        get_uraiden_contract([token.address, 2 ** 32, []])
    with pytest.raises(TypeError):
        get_uraiden_contract([0x0, CHALLENGE_PERIOD_MIN, []])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([EMPTY_ADDRESS, CHALLENGE_PERIOD_MIN, []])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([A, CHALLENGE_PERIOD_MIN, []])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([token.address, 0, []])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([token.address, CHALLENGE_PERIOD_MIN - 1, []])
    with pytest.raises(tester.TransactionFailed):
        get_uraiden_contract([fake_token.address, CHALLENGE_PERIOD_MIN, []])

    uraiden = get_uraiden_contract([token.address, 2 ** 32 - 1, []])
    assert is_same_address(uraiden.call().owner_address(), owner)
    assert is_same_address(uraiden.call().token(), token.address)
    assert uraiden.call().challenge_period() == 2 ** 32 - 1
    assert token.call().balanceOf(uraiden.address) == 0
    assert web3.eth.getBalance(uraiden.address) == 0

    # Temporary limit for the bug bounty release
    assert uraiden.call().channel_deposit_bugbounty_limit() == CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT


def test_variable_access(owner, uraiden_contract, token_instance, contract_params):
    uraiden = uraiden_contract(token_instance)
    assert is_same_address(uraiden.call().owner_address(), owner)
    assert is_same_address(uraiden.call().token(), token_instance.address)
    assert uraiden.call().challenge_period() == contract_params['challenge_period']
    assert uraiden.call().version() == URAIDEN_CONTRACT_VERSION
    assert uraiden.call().channel_deposit_bugbounty_limit() == CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT


def test_function_access(
    owner,
    get_accounts,
    uraiden_contract,
    uraiden_instance,
    token_instance,
    get_channel
):
    (A, B, C, D) = get_accounts(4)
    channel = get_channel(uraiden_instance, token_instance, 100, A, B)[:3]
    (sender, receiver, open_block_number) = channel

    uraiden_instance.call().getKey(*channel)
    uraiden_instance.call().getChannelInfo(*channel)

    # even if TransactionFailed , this means the function is public / external
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().extractBalanceProofSignature(
            receiver,
            open_block_number,
            10,
            encode_hex(bytearray(65))
        )
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().tokenFallback(sender, 10, encode_hex(bytearray(20)))
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': C}).createChannel(D, 10)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().topUp(receiver, open_block_number, 10)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().uncooperativeClose(receiver, open_block_number, 10)
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact().cooperativeClose(
            receiver,
            open_block_number,
            10,
            encode_hex(bytearray(65)),
            encode_hex(bytearray(65))
        )
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


def test_version(
    web3,
    owner,
    get_accounts,
    get_uraiden_contract,
    uraiden_instance,
    token_instance
):
    (A, B) = get_accounts(2)
    other_contract = get_uraiden_contract(
        [token_instance.address, CHALLENGE_PERIOD_MIN, []],
        {'from': A}
    )
    assert other_contract is not None

    assert uraiden_instance.call().version() == URAIDEN_CONTRACT_VERSION


def test_get_channel_info(web3, get_accounts, uraiden_instance, token_instance, get_channel):
    (A, B, C, D) = get_accounts(4)
    channel = get_channel(uraiden_instance, token_instance, 100, C, D)[:3]
    (sender, receiver, open_block_number) = channel

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number - 2)
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
    assert channel_data[4] == 0

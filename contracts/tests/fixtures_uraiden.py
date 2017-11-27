import pytest
from ethereum import tester
from tests.utils import print_logs
from tests.fixtures import (
    owner_index,
    owner,
    contract_params,
    create_contract,
    get_token_contract,
    event_handler,
    print_gas,
    txn_gas,
    uraiden_events,
    get_block
)


print_the_logs = False


@pytest.fixture()
def get_uraiden_contract(chain, create_contract):
    def get(arguments, transaction=None):
        RaidenMicroTransferChannels = chain.provider.get_contract_factory(
            'RaidenMicroTransferChannels'
        )

        uraiden_contract = create_contract(
            RaidenMicroTransferChannels,
            arguments,
            transaction
        )

        if print_the_logs:
            print_logs(uraiden_contract, 'ChannelCreated', 'RaidenMicroTransferChannels')
            print_logs(uraiden_contract, 'ChannelToppedUp', 'RaidenMicroTransferChannels')
            print_logs(uraiden_contract, 'ChannelCloseRequested', 'RaidenMicroTransferChannels')
            print_logs(uraiden_contract, 'ChannelSettled', 'RaidenMicroTransferChannels')

        return uraiden_contract
    return get


@pytest.fixture()
def token_contract(contract_params, get_token_contract):
    def get(transaction=None):
        args = [
            10 ** 26,
            'CustomToken',
            'TKN',
            contract_params['decimals']
        ]
        token_contract = get_token_contract(args, transaction)
        return token_contract
    return get


@pytest.fixture()
def token_instance(token_contract):
    return token_contract()


@pytest.fixture
def uraiden_contract(contract_params, token_instance, get_uraiden_contract):
    def get(token=None, transaction=None):
        if not token:
            token = token_instance
        uraiden_contract = get_uraiden_contract(
            [token.address, contract_params['challenge_period']]
        )
        return uraiden_contract
    return get


@pytest.fixture
def uraiden_instance(uraiden_contract):
    return uraiden_contract()



@pytest.fixture(params=['20', '223'])
def get_channel(web3, request, owner, get_accounts, event_handler, print_gas, txn_gas, get_block):
    def get(uraiden_instance, token_instance, deposit, sender=None, receiver=None):
        contract_type = request.param
        ev_handler = event_handler(uraiden_instance)
        gas_used_create = 0

        if not sender:
            (sender, receiver) = get_accounts(2)

        # Supply accounts with tokens
        token_instance.transact({"from": owner}).transfer(sender, deposit + 500)
        token_instance.transact({"from": owner}).transfer(receiver, 100)

        # Memorize balances for tests
        uraiden_pre_balance = token_instance.call().balanceOf(uraiden_instance.address)
        sender_pre_balance = token_instance.call().balanceOf(sender)
        receiver_pre_balance = token_instance.call().balanceOf(receiver)

        # Create channel (ERC20 or ERC223 logic)
        if contract_type == '20':
            txn_hash = token_instance.transact({"from": sender}).approve(uraiden_instance.address, deposit)
            gas_used_create += txn_gas(txn_hash)
            txn_hash = uraiden_instance.transact({"from": sender}).createChannelERC20(receiver, deposit)
            message = 'test_channel_20_create'
        else:
            txdata = receiver[2:].zfill(40)
            txdata = bytes.fromhex(txdata)
            txn_hash = token_instance.transact({"from": sender}).transfer(uraiden_instance.address, deposit, txdata)
            message = 'test_channel_223_create'

        # Check token balances post channel creation
        assert token_instance.call().balanceOf(uraiden_instance.address) == uraiden_pre_balance + deposit
        assert token_instance.call().balanceOf(sender) == sender_pre_balance - deposit
        assert token_instance.call().balanceOf(receiver) == receiver_pre_balance

        # Check creation event
        ev_handler.add(txn_hash, uraiden_events['created'], checkCreatedEvent(sender, receiver, deposit))
        ev_handler.check()

        open_block_number = get_block(txn_hash)
        channel_data = uraiden_instance.call().getChannelInfo(sender, receiver, open_block_number)
        assert channel_data[0] == uraiden_instance.call().getKey(sender, receiver, open_block_number)
        assert channel_data[1] == deposit
        assert channel_data[2] == 0
        assert channel_data[3] == 0

        print_gas(txn_hash, message, gas_used_create)

        return (sender, receiver, open_block_number)
    return get


def channel_settle_tests(uraiden_instance, token, channel):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    # TODO: why this fails?
    # token.transact({"from": sender}).approve(uraiden_instance.address, 33)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUpERC20(receiver, open_block_number, 33)


def channel_pre_close_tests(uraiden_instance, token, channel, top_up_deposit=0):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    token.transact({"from": sender}).approve(uraiden_instance.address, 33)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    uraiden_instance.transact({'from': sender}).topUpERC20(receiver, open_block_number, top_up_deposit)


def checkCreatedEvent(sender, receiver, deposit):
    def get(event):
        assert event['args']['_sender'] == sender
        assert event['args']['_receiver'] == receiver
        assert event['args']['_deposit'] == deposit
    return get


def checkToppedUpEvent(sender, receiver, open_block_number, added_deposit, deposit):
    def get(event):
        assert event['args']['_sender'] == sender
        assert event['args']['_receiver'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_deposit'] == deposit
        assert event['args']['_added_deposit'] == added_deposit
    return get


def checkClosedEvent(sender, receiver, open_block_number, balance):
    def get(event):
        assert event['args']['_sender'] == sender
        assert event['args']['_receiver'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_balance'] == balance
    return get


def checkSettledEvent(sender, receiver, open_block_number, balance):
    def get(event):
        assert event['args']['_sender'] == sender
        assert event['args']['_receiver'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_balance'] == balance
    return get

import pytest
from ethereum import tester
from utils import sign
from tests.utils import (
    print_logs,
    balance_proof_hash,
    closing_message_hash
)
from tests.fixtures import (
    print_the_logs,
    channel_params,
    owner_index,
    owner,
    contract_params,
    create_contract,
    get_token_contract,
    get_block
)


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
            print_logs(uraiden_contract, 'ChannelWithdraw', 'RaidenMicroTransferChannels')

        return uraiden_contract
    return get


@pytest.fixture()
def token_contract(contract_params, get_token_contract):
    def get(transaction=None):
        args = [contract_params['supply'], 'CustomToken', 'TKN', contract_params['decimals']]
        token_contract = get_token_contract(args, transaction)
        return token_contract
    return get


@pytest.fixture()
def token_instance(token_contract):
    return token_contract()


@pytest.fixture()
def delegate_contract(chain, owner, create_contract):
    def get(transaction=None):
        Delegate = chain.provider.get_contract_factory('Delegate')
        delegate_contract = create_contract(Delegate, [], {})
        return delegate_contract
    return get


@pytest.fixture()
def delegate_instance(delegate_contract):
    return delegate_contract()


@pytest.fixture
def uraiden_contract(contract_params, token_instance, get_uraiden_contract):
    def get(token=None, trusted_contracts=[], transaction=None):
        if not token:
            token = token_instance
        uraiden_contract = get_uraiden_contract(
            [token.address, contract_params['challenge_period'], trusted_contracts]
        )
        return uraiden_contract
    return get


@pytest.fixture
def uraiden_instance(owner, uraiden_contract, token_instance, delegate_instance):
    uraiden_instance = uraiden_contract(
        token_instance,
        [delegate_instance.address]
    )
    delegate_instance.transact({'from': owner}).setup(
        token_instance.address,
        uraiden_instance.address
    )
    return uraiden_instance


@pytest.fixture
def get_channel(channel_params, owner, get_accounts, uraiden_instance, token_instance, get_block):
    def get(uraiden=None, token=None, deposit=None, sender=None, receiver=None, contract_type=None):
        deposit = deposit or channel_params['deposit']
        contract_type = contract_type or channel_params['type']
        balance = channel_params['balance']
        uraiden = uraiden or uraiden_instance
        token = token or token_instance

        if not sender:
            (sender, receiver) = get_accounts(2)

        # Supply accounts with tokens
        token.transact({"from": owner}).transfer(sender, deposit + 500)
        token.transact({"from": owner}).transfer(receiver, 100)

        # Create channel (ERC20 or ERC223 logic)
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

        open_block_number = get_block(txn_hash)

        balance_message_hash = balance_proof_hash(
            receiver,
            open_block_number,
            balance,
            uraiden_instance.address
        )
        balance_msg_sig, addr = sign.check(balance_message_hash, tester.k2)

        closing_msg_hash = closing_message_hash(
            sender,
            open_block_number,
            balance,
            uraiden_instance.address
        )
        closing_sig, addr = sign.check(closing_msg_hash, tester.k3)

        return (sender, receiver, open_block_number, balance_msg_sig, closing_sig)
    return get


def channel_settle_tests(uraiden_instance, token, channel):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    # TODO: why this fails?
    # token.transact({"from": sender}).approve(uraiden_instance.address, 33)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).topUp(receiver, open_block_number, 33)


def channel_pre_close_tests(uraiden_instance, token, channel, top_up_deposit=0):
    (sender, receiver, open_block_number) = channel

    # Approve token allowance
    token.transact({"from": sender}).approve(uraiden_instance.address, 33)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': sender}).settle(receiver, open_block_number)

    uraiden_instance.transact({'from': sender}).topUp(
        receiver,
        open_block_number,
        top_up_deposit
    )


def checkCreatedEvent(sender, receiver, deposit):
    def get(event):
        assert event['args']['_sender_address'] == sender
        assert event['args']['_receiver_address'] == receiver
        assert event['args']['_deposit'] == deposit
    return get


def checkToppedUpEvent(sender, receiver, open_block_number, added_deposit, deposit):
    def get(event):
        assert event['args']['_sender_address'] == sender
        assert event['args']['_receiver_address'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_added_deposit'] == added_deposit
    return get


def checkClosedEvent(sender, receiver, open_block_number, balance):
    def get(event):
        assert event['args']['_sender_address'] == sender
        assert event['args']['_receiver_address'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_balance'] == balance
    return get


def checkSettledEvent(sender, receiver, open_block_number, balance, receiver_tokens):
    def get(event):
        assert event['args']['_sender_address'] == sender
        assert event['args']['_receiver_address'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_balance'] == balance
        assert event['args']['_receiver_tokens'] == receiver_tokens
    return get


def checkTrustedEvent(contract_address, trusted_status):
    def get(event):
        assert event['args']['_trusted_contract_address'] == contract_address
        assert event['args']['_trusted_status'] == trusted_status
    return get


def checkWithdrawEvent(sender, receiver, open_block_number, withdrawn_balance):
    def get(event):
        assert event['args']['_sender_address'] == sender
        assert event['args']['_receiver_address'] == receiver
        assert event['args']['_open_block_number'] == open_block_number
        assert event['args']['_withdrawn_balance'] == withdrawn_balance
    return get

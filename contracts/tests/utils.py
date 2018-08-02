import pytest
from ethereum import tester
from utils.sign import eth_signed_typed_data_message


def balance_proof_hash(receiver, block, balance, contract):
    return eth_signed_typed_data_message(
        ('string', 'address', ('uint', 32), ('uint', 192), 'address'),
        ('message_id', 'receiver', 'block_created', 'balance', 'contract'),
        ('Sender balance proof signature', receiver, block, balance, contract)
    )


def closing_message_hash(sender, block, balance, contract):
    return eth_signed_typed_data_message(
        ('string', 'address', ('uint', 32), ('uint', 192), 'address'),
        ('message_id', 'sender', 'block_created', 'balance', 'contract'),
        ('Receiver closing signature', sender, block, balance, contract)
    )


def print_logs(contract, event, name=''):
    transfer_filter_past = contract.pastEvents(event)
    past_events = transfer_filter_past.get()
    if len(past_events):
        print('--(', name, ') past events for ', event, past_events)

    transfer_filter = contract.on(event)
    events = transfer_filter.get()
    if len(events):
        print('--(', name, ') events for ', event, events)

    transfer_filter.watch(lambda x: print('--(', name, ') event ', event, x['args']))


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

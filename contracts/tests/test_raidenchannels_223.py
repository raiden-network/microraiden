import pytest
from populus.utils.wait import wait_for_transaction_receipt
from web3.utils.compat import (
    Timeout,
)
from ethereum import tester
import sign


def save_logs(contract, event_name):
    logs[event_name] = []

    def add(log):
        logs[event_name].append(log)

    transfer_filter_past = contract.pastEvents(event_name)
    past_events = transfer_filter_past.get()
    for event in past_events:
        add(event)

    transfer_filter = contract.on(event_name)
    # wait(transfer_filter)
    events = transfer_filter.get()
    for event in events:
        add(event)
    transfer_filter.watch(lambda x: add(x))


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


@pytest.fixture
def contract(chain, web3):
    global token
    global logs
    global challenge_period
    challenge_period = 5
    logs = {}
    (A, B, C) = web3.eth.accounts[:3]
    RDNToken = chain.provider.get_contract_factory('RDNToken')
    deploy_txn_hash = RDNToken.deploy(args=[10000, "RDN", 2, "R"])
    token_address = chain.wait.for_contract_address(deploy_txn_hash)
    token = RDNToken(token_address)

    print_logs(token, 'Transfer', 'RDNToken')

    RaidenMicroTransferChannels = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
    deploy_txn_hash = RaidenMicroTransferChannels.deploy(args=[token_address, challenge_period])
    address = chain.wait.for_contract_address(deploy_txn_hash)
    print('RaidenMicroTransferChannels contract address', address)

    contract = RaidenMicroTransferChannels(address)
    print_logs(contract, 'TokenFallback', 'RaidenMicroTransferChannels')
    print_logs(contract, 'ChannelCreated', 'RaidenMicroTransferChannels')

    return contract


def test_channel_create(web3, contract):
    (Owner, B, C) = web3.eth.accounts[:3]
    global channel_deposit
    channel_deposit = 50

    # addr_bytes = web3.toAscii(C)
    addr_bytes = bytes(C, "raw_unicode_escape")
    print('transfer', contract.address, channel_deposit, addr_bytes)

    token.transact({"from": Owner}).transfer(B, 250)
    assert token.call().balanceOf(B) == 250
    token.transact({"from": B}).transfer(contract.address, channel_deposit, addr_bytes)

    save_logs(contract, 'ChannelCreated')
    with Timeout(20) as timeout:
        timeout.sleep(2)

    open_block_number = logs['ChannelCreated'][0]['blockNumber']

    channel_data = contract.call().getChannelInfo(B, C, open_block_number)

    print('channel_data', channel_data)
    assert channel_data[0] == contract.call().getKey(B, C, open_block_number)
    assert channel_data[1] == channel_deposit
    assert channel_data[2] == 0
    assert channel_data[3] == 0

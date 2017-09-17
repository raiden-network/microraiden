import pytest

from eth_utils import (
    encode_hex,
)
from ethereum.tester import TransactionFailed
from web3.exceptions import BadFunctionCallOutput

from microraiden.close_all_channels import close_open_channels


def test_close_simple(client, channel_manager, web3, wait_for_blocks):
    sender = client.account
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 2,
                                     encode_hex(channel.create_transfer(2)))

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    contract_proxy = channel_manager.contract_proxy
    tx_count_before = web3.eth.getTransactionCount(receiver)
    close_open_channels(state, contract_proxy, 10, wait=lambda: wait_for_blocks(1))
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before + 1

    with pytest.raises((BadFunctionCallOutput, TransactionFailed)):
        channel_id = (channel.sender, channel.receiver, channel.block)
        contract_proxy.contract.call().getChannelInfo(*channel_id)
    wait_for_blocks(1)


def test_close_topup(client, channel_manager, web3, wait_for_blocks):
    sender = client.account
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel.topup(5)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 12,
                                     encode_hex(channel.create_transfer(12)))

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    contract_proxy = channel_manager.contract_proxy
    tx_count_before = web3.eth.getTransactionCount(receiver)
    close_open_channels(state, contract_proxy, 10, wait=lambda: wait_for_blocks(1))
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before + 1

    with pytest.raises((BadFunctionCallOutput, TransactionFailed)):
        channel_id = (channel.sender, channel.receiver, channel.block)
        contract_proxy.contract.call().getChannelInfo(*channel_id)
    wait_for_blocks(1)


def test_close_valid_close(client, channel_manager, web3, wait_for_blocks):
    sender = client.account
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 2,
                                     encode_hex(channel.create_transfer(2)))
    channel.close()

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    contract_proxy = channel_manager.contract_proxy

    tx_count_before = web3.eth.getTransactionCount(receiver)
    close_open_channels(state, contract_proxy, 10, wait=lambda: wait_for_blocks(1))
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before + 1

    with pytest.raises((BadFunctionCallOutput, TransactionFailed)):
        channel_id = (channel.sender, channel.receiver, channel.block)
        contract_proxy.contract.call().getChannelInfo(*channel_id)
    wait_for_blocks(1)


def test_close_invalid_close(client, channel_manager, web3, wait_for_blocks):
    sender = client.account
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 2,
                                     encode_hex(channel.create_transfer(2)))
    # cheat
    channel.balance = 0
    channel.create_transfer(1)
    channel.close()

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    contract_proxy = channel_manager.contract_proxy

    tx_count_before = web3.eth.getTransactionCount(receiver)
    close_open_channels(state, contract_proxy, 10, wait=lambda: wait_for_blocks(1))
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before + 1

    with pytest.raises((BadFunctionCallOutput, TransactionFailed)):
        channel_id = (channel.sender, channel.receiver, channel.block)
        contract_proxy.contract.call().getChannelInfo(*channel_id)
    wait_for_blocks(1)


def test_close_settled(client, channel_manager, web3, wait_for_blocks):
    sender = client.account
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 2,
                                     encode_hex(channel.create_transfer(2)))
    receiver_sig = channel_manager.sign_close(sender, channel.block, 2)
    channel.close_cooperatively(receiver_sig)
    wait_for_blocks(channel_manager.n_confirmations + 1)

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    contract_proxy = channel_manager.contract_proxy

    tx_count_before = web3.eth.getTransactionCount(receiver)
    close_open_channels(state, contract_proxy, 10, wait=lambda: wait_for_blocks(1))
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before
    wait_for_blocks(1)

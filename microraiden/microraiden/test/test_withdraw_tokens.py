from eth_utils import (
    encode_hex,
)
from web3 import Web3

from microraiden import Client
from microraiden.channel_manager import ChannelManager
from microraiden.withdraw_tokens import withdraw_from_channels


def test_withdraw_below_minimum(
        client: Client,
        channel_manager: ChannelManager,
        web3: Web3,
        wait_for_blocks
):
    sender = client.context.address
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 2,
                                     encode_hex(channel.create_transfer(2)))

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    tx_count_before = web3.eth.getTransactionCount(receiver)
    withdraw_from_channels(
        channel_manager.private_key,
        state,
        channel_manager.channel_manager_contract,
        3,
        wait=lambda: wait_for_blocks(1)
    )
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before

    channel_id = (channel.sender, channel.receiver, channel.block)
    channel_info = channel_manager.channel_manager_contract.call().getChannelInfo(*channel_id)
    _, deposit, settle_block_number, closing_balance, transferred_tokens = channel_info
    assert transferred_tokens == 0

    wait_for_blocks(1)


def test_withdraw_above_minimum(
        client: Client,
        channel_manager: ChannelManager,
        web3: Web3,
        wait_for_blocks
):
    sender = client.context.address
    receiver = channel_manager.receiver

    channel = client.open_channel(receiver, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    channel_manager.register_payment(sender, channel.block, 4,
                                     encode_hex(channel.create_transfer(4)))

    channel_manager.stop()  # don't update state from this point on
    channel_manager.join()
    state = channel_manager.state
    tx_count_before = web3.eth.getTransactionCount(receiver)
    withdraw_from_channels(
        channel_manager.private_key,
        state,
        channel_manager.channel_manager_contract,
        3,
        wait=lambda: wait_for_blocks(1)
    )
    tx_count_after = web3.eth.getTransactionCount(receiver)
    assert tx_count_after == tx_count_before + 1

    channel_id = (channel.sender, channel.receiver, channel.block)
    channel_info = channel_manager.channel_manager_contract.call().getChannelInfo(*channel_id)
    _, deposit, settle_block_number, closing_balance, transferred_tokens = channel_info
    assert transferred_tokens == 4

    wait_for_blocks(1)

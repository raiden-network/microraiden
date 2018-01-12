import logging
from itertools import count
from typing import List

from eth_utils import is_same_address, encode_hex
from web3 import Web3
from web3.contract import Contract

from microraiden import Client
from microraiden.client import Channel
from microraiden.utils import get_logs, sign_balance_proof, privkey_to_addr
from microraiden.exceptions import InvalidBalanceProof, NoOpenChannel, InvalidBalanceAmount
from microraiden.test.fixtures.channel_manager import start_channel_manager
from microraiden.channel_manager import ChannelManager
from microraiden.test.config import (
    RECEIVER_ETH_ALLOWANCE,
    RECEIVER_TOKEN_ALLOWANCE
)
import gevent
import pytest

log = logging.getLogger(__name__)


@pytest.fixture
def confirmed_open_channel(
        channel_manager: ChannelManager,
        client: Client,
        receiver_address: str,
        wait_for_blocks
):
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(channel_manager.n_confirmations + 1)
    gevent.sleep(channel_manager.blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager.channels

    return channel


def test_channel_opening(
        client: Client,
        web3: Web3,
        make_account,
        private_keys: List[str],
        channel_manager_contract,
        token_contract,
        mine_sync_event,
        wait_for_blocks,
        use_tester,
        state_db_path
):
    receiver1_privkey = make_account(
        RECEIVER_ETH_ALLOWANCE,
        RECEIVER_TOKEN_ALLOWANCE,
        private_keys[2]
    )
    receiver2_privkey = make_account(
        RECEIVER_ETH_ALLOWANCE,
        RECEIVER_TOKEN_ALLOWANCE,
        private_keys[3]
    )
    receiver_address = privkey_to_addr(receiver1_privkey)
    # make sure channel_manager1 is terminated properly, otherwise Blockchain will be running
    #  in the background, ruining other tests' results
    channel_manager1 = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver1_privkey,
        n_confirmations=5,
        state_filename=state_db_path
    )
    start_channel_manager(channel_manager1, use_tester, mine_sync_event)

    channel_manager2 = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver2_privkey,
        n_confirmations=5,
        state_filename=state_db_path
    )
    start_channel_manager(channel_manager2, use_tester, mine_sync_event)
    channel_manager1.wait_sync()
    channel_manager2.wait_sync()
    blockchain = channel_manager1.blockchain
    channel = client.open_channel(receiver_address, 10)
    # should be in unconfirmed channels
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) not in channel_manager1.channels
    assert (channel.sender, channel.block) in channel_manager1.unconfirmed_channels
    channel_rec = channel_manager1.unconfirmed_channels[channel.sender, channel.block]
    assert is_same_address(channel_rec.receiver, receiver_address)
    assert is_same_address(channel_rec.sender, channel.sender)
    assert channel_rec.mtime == channel_rec.ctime

    # should be confirmed after n blocks
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager1.channels
    channel_rec = channel_manager1.channels[channel.sender, channel.block]
    assert is_same_address(channel_rec.receiver, receiver_address)
    assert is_same_address(channel_rec.sender, channel.sender)
    assert channel_rec.balance == 0
    assert channel_rec.last_signature is None
    assert channel_rec.is_closed is False
    assert channel_rec.settle_timeout == -1

    # should not appear in other channel manager
    assert (channel.sender, channel.block) not in channel_manager2.channels
    assert (channel.sender, channel.block) not in channel_manager2.unconfirmed_channels
    channel_manager1.stop()
    channel_manager2.stop()


def test_close_unconfirmed_event(
        channel_manager: ChannelManager,
        client: Client,
        receiver_address: str,
        wait_for_blocks
):
    channel_manager.wait_sync()
    blockchain = channel_manager.blockchain
    # if unconfirmed channel is closed it should simply be forgotten
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager.unconfirmed_channels
    assert (channel.sender, channel.block) not in channel_manager.channels
    channel.close()
    wait_for_blocks(channel_manager.blockchain.n_confirmations)  # opening confirmed
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) not in channel_manager.unconfirmed_channels
    assert (channel.sender, channel.block) in channel_manager.channels
    wait_for_blocks(1)  # closing confirmed
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) not in channel_manager.unconfirmed_channels
    assert (channel.sender, channel.block) in channel_manager.channels


def test_close_confirmed_event(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        wait_for_blocks
):
    blockchain = channel_manager.blockchain
    channel_manager.wait_sync()

    confirmed_open_channel.close()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)

    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.is_closed is True

    settle_block = channel_manager.channel_manager_contract.call().getChannelInfo(
        channel_rec.sender,
        channel_rec.receiver,
        channel_rec.open_block_number
    )[2]
    assert channel_rec.settle_timeout == settle_block


def test_channel_settled_event(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        wait_for_blocks,
        web3: Web3,
        use_tester: bool
):
    if not use_tester:
        pytest.skip('This test takes several hours on real blockchains.')

    blockchain = channel_manager.blockchain
    channel_manager.wait_sync()
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    confirmed_open_channel.close()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager.channels[channel_id]
    wait_for_blocks(channel_rec.settle_timeout - web3.eth.blockNumber)
    gevent.sleep(blockchain.poll_interval)
    assert web3.eth.blockNumber >= channel_rec.settle_timeout
    assert channel_id in channel_manager.channels
    confirmed_open_channel.settle()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert channel_id not in channel_manager.channels


def test_topup(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        wait_for_blocks
):
    blockchain = channel_manager.blockchain
    channel_manager.wait_sync()

    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    confirmed_open_channel.topup(5)

    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)

    channel_rec = channel_manager.channels[channel_id]
    topup_txs = channel_rec.unconfirmed_topups
    assert len(topup_txs) == 1 and list(topup_txs.values())[0] == 5

    wait_for_blocks(channel_manager.blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)

    channel_rec = channel_manager.channels[channel_id]
    topup_txs = channel_rec.unconfirmed_topups
    assert len(topup_txs) == 0
    assert channel_rec.deposit == 15


def test_unconfirmed_topup(
        channel_manager: ChannelManager,
        client: Client,
        receiver_address: str,
        wait_for_blocks
):
    blockchain = channel_manager.blockchain
    channel_manager.wait_sync()
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager.unconfirmed_channels
    channel.topup(5)
    wait_for_blocks(channel_manager.blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager.channels
    channel_rec = channel_manager.channels[channel.sender, channel.block]
    assert channel_rec.deposit == 15


def test_payment(
        channel_manager: ChannelManager,
        confirmed_open_channel,
        receiver_address: str,
        receiver_privkey: str,
        sender_privkey: str,
        sender_address: str
):
    channel_manager.wait_sync()
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.last_signature is None
    assert channel_rec.balance == 0

    # valid transfer
    sig1 = encode_hex(confirmed_open_channel.create_transfer(2))
    channel_manager.register_payment(sender_address, channel_rec.open_block_number, 2, sig1)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 2
    assert channel_rec.last_signature == sig1

    # transfer signed with wrong private key
    invalid_sig = encode_hex(sign_balance_proof(
        receiver_privkey,  # should be sender's privkey
        channel_rec.receiver,
        channel_rec.open_block_number,
        4,
        channel_manager.channel_manager_contract.address
    ))
    with pytest.raises(InvalidBalanceProof):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number, 4,
                                         invalid_sig)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 2
    assert channel_rec.last_signature == sig1

    # transfer to different receiver
    invalid_sig = encode_hex(sign_balance_proof(
        sender_privkey,
        sender_address,  # should be receiver's address
        channel_rec.open_block_number,
        4,
        channel_manager.channel_manager_contract.address
    ))
    with pytest.raises(InvalidBalanceProof):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number, 4,
                                         invalid_sig)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 2
    assert channel_rec.last_signature == sig1

    # transfer negative amount
    invalid_sig = encode_hex(sign_balance_proof(
        sender_privkey,
        receiver_address,
        channel_rec.open_block_number,
        1,  # should be greater than 2
        channel_manager.channel_manager_contract.address
    ))
    with pytest.raises(InvalidBalanceAmount):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number, 1,
                                         invalid_sig)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 2
    assert channel_rec.last_signature == sig1

    # parameters should match balance proof
    sig2 = encode_hex(confirmed_open_channel.create_transfer(2))
    with pytest.raises(NoOpenChannel):
        channel_manager.register_payment(receiver_address, channel_rec.open_block_number,
                                         4, sig2)
    with pytest.raises(NoOpenChannel):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number + 1,
                                         4, sig2)
    with pytest.raises(InvalidBalanceProof):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number,
                                         5, sig2)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 2
    assert channel_rec.last_signature == sig1
    channel_manager.register_payment(sender_address, channel_rec.open_block_number, 4, sig2)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 4
    assert channel_rec.last_signature == sig2

    # should transfer up to deposit
    sig3 = encode_hex(confirmed_open_channel.create_transfer(6))
    channel_manager.register_payment(sender_address, channel_rec.open_block_number, 10, sig3)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.balance == 10
    assert channel_rec.last_signature == sig3

    # transfer too much
    invalid_sig = encode_hex(sign_balance_proof(
        sender_privkey,
        receiver_address,
        channel_rec.open_block_number,
        12,  # should not be greater than 10
        channel_manager.channel_manager_contract.address
    ))
    with pytest.raises(InvalidBalanceProof):
        channel_manager.register_payment(sender_address, channel_rec.open_block_number, 12,
                                         invalid_sig)
    assert channel_rec.balance == 10
    assert channel_rec.last_signature == sig3


def test_challenge(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        receiver_address: str,
        sender_address: str,
        wait_for_blocks,
        web3: Web3,
        client: Client
):
    blockchain = channel_manager.blockchain
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    sig = encode_hex(confirmed_open_channel.create_transfer(5))
    channel_manager.register_payment(sender_address, confirmed_open_channel.block, 5, sig)
    # hack channel to decrease balance
    confirmed_open_channel.update_balance(0)
    sig = confirmed_open_channel.create_transfer(3)
    block_before = web3.eth.blockNumber
    confirmed_open_channel.close()
    # should challenge and immediately settle
    for waited_blocks in count():
        logs = get_logs(client.context.token, 'Transfer', from_block=block_before - 1)
        if logs:
            break
        wait_for_blocks(1)
        assert waited_blocks < 10

    assert len([l for l in logs
                if is_same_address(l['args']['_to'], receiver_address) and
                l['args']['_value'] == 5]) == 1
    assert len([l for l in logs
                if is_same_address(l['args']['_to'], sender_address) and
                l['args']['_value'] == 5]) == 1
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert channel_id not in channel_manager.channels

    # update channel state so that it will not be closed twice
    client.sync_channels()
    new_state = None
    for channel in client.channels:
        if all(channel.sender == confirmed_open_channel.sender,
               channel.receiver == confirmed_open_channel.receiver,
               channel.block == confirmed_open_channel.block):
            new_state = channel.state
    if new_state is None:
        confirmed_open_channel.state = confirmed_open_channel.State.closed
    else:
        confirmed_open_channel.state = new_state


def test_multiple_topups(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        wait_for_blocks
):
    blockchain = channel_manager.blockchain
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    channel_rec = channel_manager.channels[channel_id]

    # first unconfirmed topup
    assert channel_rec.deposit == 10
    confirmed_open_channel.topup(5)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)

    channel_rec = channel_manager.channels[channel_id]
    assert len(channel_rec.unconfirmed_topups) == 1
    assert list(channel_rec.unconfirmed_topups.values()) == [5]
    assert channel_rec.deposit == 10

    # second unconfirmed_topups
    confirmed_open_channel.topup(10)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager.channels[channel_id]
    assert len(channel_rec.unconfirmed_topups) >= 1  # equality if first is confirmed
    assert 10 in channel_rec.unconfirmed_topups.values()
    assert channel_rec.deposit in [10, 15]  # depends if first topup is confirmed or not

    # wait for confirmations
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager.channels[channel_id]
    assert len(channel_rec.unconfirmed_topups) == 0
    assert channel_rec.deposit == 25


def test_settlement(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        receiver_address: str,
        wait_for_blocks,
        web3: Web3,
        token_contract: Contract,
        sender_address: str,
        use_tester: bool
):
    if not use_tester:
        pytest.skip('This test takes several hours on real blockchains.')

    blockchain = channel_manager.blockchain
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)

    sig = encode_hex(confirmed_open_channel.create_transfer(2))
    channel_manager.register_payment(sender_address, confirmed_open_channel.block, 2, sig)

    confirmed_open_channel.close()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    block_before = web3.eth.blockNumber
    channel_rec = channel_manager.channels[channel_id]
    wait_for_blocks(channel_rec.settle_timeout - block_before)
    confirmed_open_channel.settle()

    logs = get_logs(token_contract, 'Transfer', from_block=block_before - 1)
    assert len([l for l in logs
                if is_same_address(l['args']['_to'], receiver_address) and
                l['args']['_value'] == 2]) == 1
    assert len([l for l in logs
                if is_same_address(l['args']['_to'], sender_address) and
                l['args']['_value'] == 8]) == 1

    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert channel_id not in channel_manager.channels


def test_cooperative(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        receiver_address: str,
        web3: Web3,
        token_contract: Contract,
        wait_for_blocks,
        sender_address: str
):
    blockchain = channel_manager.blockchain
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)

    sig1 = encode_hex(confirmed_open_channel.create_transfer(5))
    channel_manager.register_payment(sender_address, confirmed_open_channel.block, 5, sig1)

    receiver_sig = channel_manager.sign_close(sender_address, confirmed_open_channel.block, 5)
    channel_rec = channel_manager.channels[channel_id]
    assert channel_rec.is_closed is True
    block_before = web3.eth.blockNumber
    confirmed_open_channel.close_cooperatively(receiver_sig)
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    logs = get_logs(token_contract, 'Transfer', from_block=block_before - 1)
    assert len([l for l in logs
                if is_same_address(l['args']['_to'], receiver_address) and
                l['args']['_value'] == 5]) == 1
    assert len([l for l in logs
                if is_same_address(l['args']['_to'], sender_address) and
                l['args']['_value'] == 5]) == 1
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert channel_id not in channel_manager.channels


def test_cooperative_wrong_balance_proof(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        sender_address: str
):
    channel_id = (confirmed_open_channel.sender, confirmed_open_channel.block)
    channel_rec = channel_manager.channels[channel_id]

    sig1 = encode_hex(confirmed_open_channel.create_transfer(5))
    channel_manager.register_payment(sender_address, confirmed_open_channel.block, 5, sig1)

    sig2 = encode_hex(confirmed_open_channel.create_transfer(1))
    with pytest.raises(InvalidBalanceProof):
        channel_manager.sign_close(sender_address, confirmed_open_channel.block, sig2)
    assert channel_rec.is_closed is False


def test_balances(
        channel_manager: ChannelManager,
        confirmed_open_channel: Channel,
        wait_for_blocks,
        sender_address: str,
        use_tester: bool
):
    blockchain = channel_manager.blockchain
    initial_liquid_balance = channel_manager.get_liquid_balance()
    initial_locked_balance = channel_manager.get_locked_balance()
    if use_tester:
        assert initial_liquid_balance == 0
        assert initial_locked_balance == 0

    sig = encode_hex(confirmed_open_channel.create_transfer(5))
    channel_manager.register_payment(sender_address, confirmed_open_channel.block, 5, sig)

    assert channel_manager.get_liquid_balance() == initial_liquid_balance
    assert channel_manager.get_locked_balance() == 5

    receiver_sig = channel_manager.sign_close(sender_address, confirmed_open_channel.block, 5)
    confirmed_open_channel.close_cooperatively(receiver_sig)
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)

    assert channel_manager.get_liquid_balance() == initial_liquid_balance + 5
    assert channel_manager.get_locked_balance() == initial_locked_balance


def test_different_receivers(
        web3: Web3,
        make_account,
        private_keys: List[str],
        channel_manager_contract: Contract,
        token_contract: Contract,
        mine_sync_event,
        client: Client,
        sender_address: str,
        wait_for_blocks,
        use_tester: bool,
        state_db_path: str
):
    if not use_tester:
        pytest.skip('This test takes several hours on real blockchains.')

    receiver1_privkey = make_account(
        RECEIVER_ETH_ALLOWANCE,
        RECEIVER_TOKEN_ALLOWANCE,
        private_keys[2]
    )
    receiver2_privkey = make_account(
        RECEIVER_ETH_ALLOWANCE,
        RECEIVER_TOKEN_ALLOWANCE,
        private_keys[3]
    )
    receiver1_address = privkey_to_addr(receiver1_privkey)
    channel_manager1 = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver1_privkey,
        n_confirmations=5,
        state_filename=state_db_path
    )
    start_channel_manager(channel_manager1, use_tester, mine_sync_event)

    channel_manager2 = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver2_privkey,
        n_confirmations=5,
        state_filename=state_db_path
    )
    start_channel_manager(channel_manager2, use_tester, mine_sync_event)
    channel_manager1.wait_sync()
    channel_manager2.wait_sync()
    blockchain = channel_manager1.blockchain

    assert channel_manager2.blockchain.n_confirmations == blockchain.n_confirmations
    assert channel_manager2.blockchain.poll_interval == blockchain.poll_interval

    # unconfirmed open
    channel = client.open_channel(receiver1_address, 10)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)

    assert (sender_address, channel.block) in channel_manager1.unconfirmed_channels
    assert (sender_address, channel.block) not in channel_manager2.unconfirmed_channels

    # confirmed open
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert (sender_address, channel.block) in channel_manager1.channels
    assert (sender_address, channel.block) not in channel_manager2.channels

    # unconfirmed topup
    channel.topup(5)
    wait_for_blocks(1)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager1.channels[sender_address, channel.block]
    assert len(channel_rec.unconfirmed_topups) == 1
    assert channel_rec.deposit == 10

    # confirmed topup
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager1.channels[sender_address, channel.block]
    assert len(channel_rec.unconfirmed_topups) == 0
    assert channel_rec.deposit == 15

    # closing
    channel.close()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    channel_rec = channel_manager1.channels[sender_address, channel.block]
    assert channel_rec.is_closed is True

    # settlement
    block_before = web3.eth.blockNumber
    wait_for_blocks(channel_rec.settle_timeout - block_before)
    channel.settle()
    wait_for_blocks(blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)
    assert (sender_address, channel.block) not in channel_manager1.channels
    channel_manager1.stop()
    channel_manager2.stop()


def test_reorg(
        web3: Web3,
        channel_manager: ChannelManager,
        client: Client,
        receiver_address: str,
        wait_for_blocks,
        use_tester: bool
):
    if not use_tester:
        pytest.skip('Chain reorg tests only work in tester chain')
    wait_for_blocks(10)
    # create unconfirmed channel
    channel_manager.wait_sync()
    snapshot_id = web3.testing.snapshot()
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(0)
    assert (channel.sender, channel.block) in channel_manager.unconfirmed_channels

    # remove unconfirmed channel opening with reorg
    web3.testing.revert(snapshot_id)
    snapshot_id = web3.testing.snapshot()
    wait_for_blocks(0)
    assert (channel.sender, channel.block) not in channel_manager.unconfirmed_channels
    web3.testing.mine(channel_manager.n_confirmations)
    assert (channel.sender, channel.block) not in channel_manager.channels

    # leave confirmed channel opening
    web3.testing.revert(snapshot_id)
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(channel_manager.n_confirmations)
    assert (channel.sender, channel.block) in channel_manager.channels
    confirmed_snapshot_id = web3.testing.snapshot()
    wait_for_blocks(3)
    web3.testing.revert(confirmed_snapshot_id)
    assert (channel.sender, channel.block) in channel_manager.channels

    # remove unconfirmed topup
    channel = client.open_channel(receiver_address, 10)
    wait_for_blocks(channel_manager.n_confirmations)
    assert (channel.sender, channel.block) in channel_manager.channels
    topup_snapshot_id = web3.testing.snapshot()
    channel.topup(5)
    wait_for_blocks(0)
    channel_rec = channel_manager.channels[channel.sender, channel.block]
    assert len(channel_rec.unconfirmed_topups) == 1
    web3.testing.revert(topup_snapshot_id)
    wait_for_blocks(0)
    assert (channel.sender, channel.block) in channel_manager.channels
    channel_rec = channel_manager.channels[channel.sender, channel.block]
    assert len(channel_rec.unconfirmed_topups) == 0

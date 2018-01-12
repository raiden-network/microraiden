import logging
import gevent
import pytest
import os

log = logging.getLogger(__name__)


@pytest.mark.skipif(
    'TEST_SKIP_TESTNET' in os.environ,
    reason="Current testnet-safe allowances don't allow for deposits of this size."
)
@pytest.mark.skip(
    reason="Current test setup doesn't support custom allowance sizes for different networks"
)
def test_big_deposit(channel_manager, client, receiver_address, wait_for_blocks):
    """Test if deposit of size bigger than int64 causes havoc when storing the state."""
    BIG_DEPOSIT = 10000000000000000000
    blockchain = channel_manager.blockchain

    channel_manager.wait_sync()
    channel = client.open_channel(receiver_address, BIG_DEPOSIT)
    wait_for_blocks(channel_manager.blockchain.n_confirmations)
    gevent.sleep(blockchain.poll_interval)

    channel_rec = channel_manager.channels[channel.sender, channel.block]
    assert channel_rec.deposit == BIG_DEPOSIT

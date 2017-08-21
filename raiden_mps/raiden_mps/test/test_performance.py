import pytest
import time
import logging
import datetime

import gevent
from eth_utils import encode_hex

from raiden_mps.client.m2m_client import M2MClient
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS, TOKEN_ADDRESS, TEST_SENDER_PRIVKEY, \
    TEST_RECEIVER_PRIVKEY
from raiden_mps.test.utils.client import close_all_channels_cooperatively

log = logging.getLogger(__name__)


@pytest.mark.parametrize('channel_manager_contract_address', [CHANNEL_MANAGER_ADDRESS])
@pytest.mark.parametrize('token_contract_address', [TOKEN_ADDRESS])
@pytest.mark.parametrize('sender_privkey', [TEST_SENDER_PRIVKEY])
def test_m2m_client(doggo_proxy, m2m_client: M2MClient, sender_address):
    logging.basicConfig(level=logging.DEBUG)

    rmp_client = m2m_client.rmp_client
    close_all_channels_cooperatively(rmp_client, TEST_RECEIVER_PRIVKEY, 0)

    requests = 1000
    m2m_client.initial_deposit = lambda x: (requests + 1) * x

    # First transfer creates channel on-chain => exclude from profiling.
    status, headers, body = m2m_client.request_resource('doggo.jpg')
    assert body.decode().strip() == '"HI I AM A DOGGO"'
    assert status == 200

    t_start = time.time()
    for i in range(requests):
        log.debug('Transfer {}'.format(i))
        status, headers, body = m2m_client.request_resource('doggo.jpg')
        assert body.decode().strip() == '"HI I AM A DOGGO"'
        assert status == 200
    t_diff = time.time() - t_start

    # These are quite some tokens, so cooperatively close with a balance of 0.
    close_all_channels_cooperatively(rmp_client, TEST_RECEIVER_PRIVKEY, 0)

    log.info("%d requests in %s (%f rps)" % (requests,
                                             datetime.timedelta(seconds=t_diff),
                                             requests / t_diff))


def test_receiver_validation(channel_manager, rmp_client, wait_for_blocks):
    n = 1000
    # open channel
    channel = rmp_client.open_channel(channel_manager.state.receiver, n)
    wait_for_blocks(channel_manager.blockchain.n_confirmations)
    gevent.sleep(channel_manager.blockchain.poll_frequency)
    assert (channel.sender, channel.block) in channel_manager.state.channels

    # prepare balance proofs
    t_start = time.time()
    balance_proofs = [encode_hex(channel.create_transfer(1)) for _ in range(n)]
    t_diff = time.time() - t_start
    log.info("%d balance proofs prepared in %s (%f / s)",
             n, datetime.timedelta(seconds=t_diff), n / t_diff)

    # validate
    t_start = time.time()
    for i, balance_proof in enumerate(balance_proofs):
        log.debug('Transfer {}'.format(i))
        sender, received = channel_manager.register_payment(
            channel.receiver,
            channel.block,
            i + 1,
            balance_proof)
        assert sender == channel.sender
        assert received == 1

    t_diff = time.time() - t_start
    log.info("%d balance proofs verified in %s (%f / s)",
             n, datetime.timedelta(seconds=t_diff), n / t_diff)

    close_all_channels_cooperatively(rmp_client, TEST_RECEIVER_PRIVKEY, 0)

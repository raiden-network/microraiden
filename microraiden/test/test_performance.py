import time
import logging
import datetime

import gevent
from eth_utils import encode_hex

from microraiden import Session

log = logging.getLogger(__name__)


def test_resource_request(doggo_proxy, http_doggo_url: str, session: Session):
    n_requests = 10
    session.initial_deposit = lambda x: (n_requests + 1) * x

    # First transfer creates channel on-chain => exclude from profiling.
    response = session.get(http_doggo_url)
    assert response.text == 'HI I AM A DOGGO'

    t_start = time.time()
    for i in range(n_requests):
        log.debug('Transfer {}'.format(i))
        response = session.get(http_doggo_url)
        assert response.text == 'HI I AM A DOGGO'
    t_diff = time.time() - t_start

    log.info("{} requests in {} ({} rps)".format(
        n_requests, datetime.timedelta(seconds=t_diff), n_requests / t_diff)
    )


def test_receiver_validation(channel_manager, client, wait_for_blocks):
    n = 100
    # open channel
    channel = client.open_channel(channel_manager.state.receiver, n)
    wait_for_blocks(channel_manager.blockchain.n_confirmations)
    gevent.sleep(channel_manager.blockchain.poll_interval)
    assert (channel.sender, channel.block) in channel_manager.channels

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
            channel.sender,
            channel.block,
            i + 1,
            balance_proof)
        assert sender == channel.sender
        assert received == 1

    t_diff = time.time() - t_start
    log.info("%d balance proofs verified in %s (%f / s)",
             n, datetime.timedelta(seconds=t_diff), n / t_diff)

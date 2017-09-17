import pytest
import time
import logging
import datetime

import gevent
from eth_utils import encode_hex

from microraiden import DefaultHTTPClient

log = logging.getLogger(__name__)


@pytest.mark.skip(reason="it takes too long")
def test_resource_request(doggo_proxy, default_http_client: DefaultHTTPClient):
    logging.basicConfig(level=logging.DEBUG)
#    logging.getLogger('testrpc.rpc').setLevel(logging.WARNING)

    requests = 1000
    default_http_client.initial_deposit = lambda x: (requests + 1) * x

    # First transfer creates channel on-chain => exclude from profiling.
    response = default_http_client.run('doggo.jpg')
    assert response.decode().strip() == '"HI I AM A DOGGO"'

    t_start = time.time()
    for i in range(requests):
        log.debug('Transfer {}'.format(i))
        response = default_http_client.run('doggo.jpg')
        assert response.decode().strip() == '"HI I AM A DOGGO"'
    t_diff = time.time() - t_start

    log.info("{} requests in {} ({} rps)".format(
        requests, datetime.timedelta(seconds=t_diff), requests / t_diff)
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

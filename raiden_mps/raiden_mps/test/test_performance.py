import pytest
import time
import logging
import datetime

from raiden_mps.examples import M2MClient
from .utils.client import close_all_channels_cooperatively

log = logging.getLogger(__name__)


def test_m2m_client(doggo_proxy, m2m_client: M2MClient):
    logging.basicConfig(level=logging.DEBUG)

    rmp_client = m2m_client.rmp_client
    close_all_channels_cooperatively(rmp_client, balance=0)

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
    close_all_channels_cooperatively(rmp_client, balance=0)

    log.info("%d requests in %s (%f rps)" % (requests,
                                             datetime.timedelta(seconds=t_diff),
                                             requests/ t_diff))

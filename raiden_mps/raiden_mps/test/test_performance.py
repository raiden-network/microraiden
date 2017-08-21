import pytest
import time
import logging
import datetime

from raiden_mps.examples import M2MClient

log = logging.getLogger(__name__)


def test_m2m_client(doggo_proxy, m2m_client: M2MClient, clean_channels):
    logging.basicConfig(level=logging.DEBUG)

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

    log.info("{} requests in {} ({} rps)".format(
        requests, datetime.timedelta(seconds=t_diff), requests/ t_diff)
    )

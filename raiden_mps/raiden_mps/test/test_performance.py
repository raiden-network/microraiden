import pytest
import time
import logging
import datetime
import random
log = logging.getLogger(__name__)


@pytest.mark.parametrize('channel_manager_contract_address',
                         ['0x4a261b3d8c4b9bd8dd9ada820db5d3d87d1df9c6'])
@pytest.mark.parametrize('token_contract_address', ['0xbde0dea8fdc36bdabf29f4899d9701da1bfa528a'])
@pytest.mark.parametrize('sender_privkey',
                         ['c76b506ea02b7afb1776f283aaad49d2a69c980227d17d730dd436ca88cd4b85'])
def test_m2m_client(doggo_proxy, m2m_client, sender_address):
    requests = 100
    t_start = time.time()
    for i in range(requests):
        x = m2m_client.request_resource('doggo.jpg', initial_deposit=lambda x: x * random.randrange(10))
        assert x.decode().strip() == '"HI I AM A DOGGO"'
    t_diff = time.time() - t_start

    log.info("%d requests in %s (%f rps)" % (requests,
                                             datetime.timedelta(seconds=t_diff),
                                             t_diff / requests))

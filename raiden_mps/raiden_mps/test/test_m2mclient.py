import logging

from raiden_mps.client import Channel
from raiden_mps.examples import M2MClient
from raiden_mps.config import TEST_SENDER_ADDR, TEST_RECEIVER_ADDR
from raiden_mps.test.utils.client import close_all_channels_cooperatively

log = logging.getLogger(__name__)


def check_response(response: tuple):
    _, _, body = response
    assert body.decode().strip() == '"HI I AM A DOGGO"'


def test_m2m_client(doggo_proxy, m2m_client: M2MClient):
    logging.basicConfig(level=logging.INFO)
    close_all_channels_cooperatively(m2m_client.client, balance=0)

    check_response(m2m_client.request_resource('doggo.jpg'))

    open_channels = [c for c in m2m_client.client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1
    channel = open_channels[0]
    assert channel == m2m_client.channel
    assert channel.balance_sig
    assert channel.balance < channel.deposit
    assert channel.sender == TEST_SENDER_ADDR
    assert channel.receiver == TEST_RECEIVER_ADDR

    close_all_channels_cooperatively(m2m_client.client, balance=0)


def test_m2m_client_topup(doggo_proxy, m2m_client: M2MClient):
    logging.basicConfig(level=logging.INFO)
    close_all_channels_cooperatively(m2m_client.client, balance=0)

    # Create a channel that has just enough capacity for one transfer.
    m2m_client.initial_deposit = lambda x: 0
    check_response(m2m_client.request_resource('doggo.jpg'))

    open_channels = [c for c in m2m_client.client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1
    channel1 = open_channels[0]
    assert channel1 == m2m_client.channel
    assert channel1.balance_sig
    assert channel1.balance == channel1.deposit

    # Do another payment. Topup should occur.
    check_response(m2m_client.request_resource('doggo.jpg'))
    open_channels = [c for c in m2m_client.client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1
    channel2 = open_channels[0]
    assert channel2 == m2m_client.channel
    assert channel2.balance_sig
    assert channel2.balance < channel2.deposit
    assert channel1 == channel2

    close_all_channels_cooperatively(m2m_client.client, balance=0)

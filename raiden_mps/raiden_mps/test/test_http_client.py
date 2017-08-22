import logging

from raiden_mps import DefaultHTTPClient
from raiden_mps.client import Channel


log = logging.getLogger(__name__)


def check_response(response: bytes):
    assert response.decode().strip() == '"HI I AM A DOGGO"'


def test_default_http_client(doggo_proxy, default_http_client: DefaultHTTPClient, clean_channels,
                             sender_address, receiver_address):
    logging.basicConfig(level=logging.INFO)

    check_response(default_http_client.run('doggo.jpg'))

    client = default_http_client.client
    open_channels = [c for c in client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1

    channel = open_channels[0]
    assert channel == default_http_client.channel
    assert channel.balance_sig
    assert channel.balance < channel.deposit
    assert channel.sender == sender_address
    assert channel.receiver == receiver_address


def test_default_http_client_topup(
        doggo_proxy, default_http_client: DefaultHTTPClient, clean_channels
):
    logging.basicConfig(level=logging.INFO)

    # Create a channel that has just enough capacity for one transfer.
    default_http_client.initial_deposit = lambda x: 0
    check_response(default_http_client.run('doggo.jpg'))

    client = default_http_client.client
    open_channels = [c for c in client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1
    channel1 = open_channels[0]
    assert channel1 == default_http_client.channel
    assert channel1.balance_sig
    assert channel1.balance == channel1.deposit

    # Do another payment. Topup should occur.
    check_response(default_http_client.run('doggo.jpg'))
    open_channels = [c for c in client.channels if c.state == Channel.State.open]
    assert len(open_channels) == 1
    channel2 = open_channels[0]
    assert channel2 == default_http_client.channel
    assert channel2.balance_sig
    assert channel2.balance < channel2.deposit
    assert channel1 == channel2

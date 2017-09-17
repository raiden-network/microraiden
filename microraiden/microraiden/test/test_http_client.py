import logging
import json

from microraiden import DefaultHTTPClient
from microraiden.test.utils.client import close_channel_cooperatively


log = logging.getLogger(__name__)


def check_response(response: bytes):
    assert response.decode().strip() == '"HI I AM A DOGGO"'


def test_default_http_client(
        doggo_proxy,
        default_http_client: DefaultHTTPClient,
        sender_address,
        receiver_privkey,
        receiver_address
):
    logging.basicConfig(level=logging.INFO)

    check_response(default_http_client.run('doggo.jpg'))

    client = default_http_client.client
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1

    channel = open_channels[0]
    assert channel == default_http_client.channel
    assert channel.balance_sig
    assert channel.balance < channel.deposit
    assert channel.sender == sender_address
    assert channel.receiver == receiver_address
    close_channel_cooperatively(channel, receiver_privkey)


def test_default_http_client_topup(
        doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey
):
    logging.basicConfig(level=logging.INFO)

    # Create a channel that has just enough capacity for one transfer.
    default_http_client.initial_deposit = lambda x: 0
    check_response(default_http_client.run('doggo.jpg'))

    client = default_http_client.client
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1
    channel1 = open_channels[0]
    assert channel1 == default_http_client.channel
    assert channel1.balance_sig
    assert channel1.balance == channel1.deposit

    # Do another payment. Topup should occur.
    check_response(default_http_client.run('doggo.jpg'))
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1
    channel2 = open_channels[0]
    assert channel2 == default_http_client.channel
    assert channel2.balance_sig
    assert channel2.balance < channel2.deposit
    assert channel1 == channel2
    close_channel_cooperatively(channel1, receiver_privkey)


def test_default_http_client_close(
    doggo_proxy, default_http_client: DefaultHTTPClient
):
    logging.basicConfig(level=logging.INFO)

    client = default_http_client.client
    check_response(default_http_client.run('doggo.jpg'))
    default_http_client.close_active_channel()
    open_channels = client.get_open_channels()
    assert len(open_channels) == 0


def test_default_http_client_existing_channel(
        doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey, receiver_address
):
    logging.basicConfig(level=logging.INFO)

    client = default_http_client.client
    channel = client.open_channel(receiver_address, 50)
    check_response(default_http_client.run('doggo.jpg'))
    assert channel.balance == 2
    assert channel.deposit == 50
    close_channel_cooperatively(channel, receiver_privkey)


def test_default_http_client_existing_channel_topup(
    doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey, receiver_address
):
    logging.basicConfig(level=logging.INFO)

    client = default_http_client.client
    default_http_client.topup_deposit = lambda x: 13
    channel = client.open_channel(receiver_address, 1)
    check_response(default_http_client.run('doggo.jpg'))
    assert channel.balance == 2
    assert channel.deposit == 13
    close_channel_cooperatively(channel, receiver_privkey)


def test_coop_close(doggo_proxy, default_http_client: DefaultHTTPClient, sender_address,
                    receiver_privkey, receiver_address):
    logging.basicConfig(level=logging.INFO)

    check_response(default_http_client.run('doggo.jpg'))

    client = default_http_client.client
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1

    channel = open_channels[0]
    import requests
    reply = requests.get('http://localhost:5000/api/1/channels/%s/%s' %
                         (channel.sender, channel.block))
    assert reply.status_code == 200
    json_reply = json.loads(reply.text)

    request_data = {'balance': json_reply['balance']}
    reply = requests.delete('http://localhost:5000/api/1/channels/%s/%s' %
                            (channel.sender, channel.block), data=request_data)

    assert reply.status_code == 200
    close_channel_cooperatively(channel, receiver_privkey)

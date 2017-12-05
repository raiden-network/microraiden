import json
import types
import pytest
from requests.exceptions import SSLError

from microraiden import DefaultHTTPClient
from microraiden.test.utils.client import close_channel_cooperatively, patch_on_http_response
from microraiden.test.utils.disable_ssl_check import disable_ssl_check


def check_response(response: bytes):
    assert response and response.decode().strip() == '"HI I AM A DOGGO"'


def test_cheating_client(
        doggo_proxy,
        default_http_client: DefaultHTTPClient
):
    """this test scenario where client sends less funds than what is requested
        by the server. In such case, a "RDN-Invalid-Amount=1" header should
        be sent in a server's reply
    """
    #  patch default http client to use price lower than the server suggests
    def patched_payment(
            self: DefaultHTTPClient,
            receiver: str,
            price: int,
            balance: int,
            balance_sig: bytes,
            channel_manager_address: str
    ):
        self.invalid_amount_received = 0
        return DefaultHTTPClient.on_payment_requested(
            self,
            receiver,
            price + self.price_adjust,
            balance,
            balance_sig,
            channel_manager_address
        )

    def patched_on_invalid_amount(self: DefaultHTTPClient):
        DefaultHTTPClient.on_invalid_amount(self)
        self.invalid_amount_received = 1

    default_http_client.on_invalid_amount = types.MethodType(
        patched_on_invalid_amount,
        default_http_client
    )
    default_http_client.on_payment_requested = types.MethodType(
        patched_payment,
        default_http_client
    )

    # correct amount
    default_http_client.price_adjust = 0
    response = default_http_client.run('doggo.jpg')
    check_response(response)
    assert default_http_client.invalid_amount_received == 0
    # underpay
    default_http_client.price_adjust = -1
    response = default_http_client.run('doggo.jpg')
    assert response is None
    assert default_http_client.invalid_amount_received == 1
    # overpay
    default_http_client.price_adjust = 1
    response = default_http_client.run('doggo.jpg')
    assert response is None
    assert default_http_client.invalid_amount_received == 1


def test_default_http_client(
        doggo_proxy,
        default_http_client: DefaultHTTPClient,
        sender_address,
        receiver_privkey,
        receiver_address
):

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
    close_channel_cooperatively(channel, receiver_privkey, client.channel_manager_address)


def test_default_http_client_topup(
        doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey
):

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
    close_channel_cooperatively(channel1, receiver_privkey, client.channel_manager_address)


def test_default_http_client_close(
    doggo_proxy, default_http_client: DefaultHTTPClient
):

    client = default_http_client.client
    check_response(default_http_client.run('doggo.jpg'))
    default_http_client.close_active_channel()
    open_channels = client.get_open_channels()
    assert len(open_channels) == 0


def test_default_http_client_existing_channel(
        doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey, receiver_address
):

    client = default_http_client.client
    channel = client.open_channel(receiver_address, 50)
    check_response(default_http_client.run('doggo.jpg'))
    assert channel.balance == 2
    assert channel.deposit == 50
    close_channel_cooperatively(channel, receiver_privkey, client.channel_manager_address)


def test_default_http_client_existing_channel_topup(
    doggo_proxy, default_http_client: DefaultHTTPClient, receiver_privkey, receiver_address
):

    client = default_http_client.client
    default_http_client.topup_deposit = lambda x: 13
    channel = client.open_channel(receiver_address, 1)
    check_response(default_http_client.run('doggo.jpg'))
    assert channel.balance == 2
    assert channel.deposit == 13
    close_channel_cooperatively(channel, receiver_privkey, client.channel_manager_address)


def test_coop_close(
        doggo_proxy,
        default_http_client: DefaultHTTPClient,
        sender_address,
        receiver_privkey,
        receiver_address
):

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
    close_channel_cooperatively(channel, receiver_privkey, client.channel_manager_address)


@pytest.mark.parametrize('proxy_ssl', [1])
def test_ssl_client(
        doggo_proxy,
        default_http_client: DefaultHTTPClient
):
    default_http_client.use_ssl = True
    with disable_ssl_check():
        check_response(default_http_client.run('doggo.jpg'))
    with pytest.raises(SSLError):
        check_response(default_http_client.run('doggo.jpg'))


def test_status_codes(doggo_proxy, default_http_client):
    patch_on_http_response(default_http_client, abort_on=[404])
    default_http_client.run('doggo.jpg')
    assert default_http_client.last_response.status_code == 200
    default_http_client.run('does-not-exist')
    assert default_http_client.last_response.status_code == 404

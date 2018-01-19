import json
import re
import types
from unittest import mock

import pytest
import requests_mock
from eth_utils import encode_hex, is_same_address
from munch import Munch
from requests import Response
from requests.exceptions import SSLError
from web3 import Web3

from microraiden import HTTPHeaders
from microraiden import Session
from microraiden.client import Channel


def check_response(response: Response):
    assert response and response.text == 'HI I AM A DOGGO'


def test_full_cycle_success(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    session.initial_deposit = lambda x: x

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '7'

        headers2 = Munch()
        headers2.cost = '7'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 200, 'headers': headers2, 'text': 'success'}
        ])
        response = session.get(url)

    # Filter out any requests made to the ethereum node.
    request_history = [request for request in server_mock.request_history if request.port == 5000]

    # First cycle, request price.
    request = request_history[0]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address

    # Second cycle, pay price.
    request = request_history[1]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '7'

    assert session.channel.balance == 7
    balance_sig_hex = encode_hex(session.channel.balance_sig)
    assert request.headers['RDN-Balance-Signature'] == balance_sig_hex
    assert session.channel.balance_sig
    assert response.text == 'success'


def test_full_cycle_adapt_balance(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    # Simulate a lost balance signature.
    client = session.client
    channel = client.get_suitable_channel(receiver_address, 10, initial_deposit=lambda x: 2 * x)
    channel.create_transfer(3)
    lost_balance_sig = channel.balance_sig
    channel.update_balance(0)

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '7'

        headers2 = headers1.copy()
        headers2.invalid_amount = '1'
        headers2.sender_balance = '3'
        headers2.balance_signature = encode_hex(lost_balance_sig)

        headers3 = Munch()
        headers3.cost = '7'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)
        headers3 = HTTPHeaders.serialize(headers3)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 402, 'headers': headers2},
            {'status_code': 200, 'headers': headers3, 'text': 'success'}
        ])

        response = session.get(url)

    # Filter out any requests made to the ethereum node.
    request_history = [request for request in server_mock.request_history if request.port == 5000]

    # First cycle, request price.
    request = request_history[0]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address

    # Second cycle, pay price based on outdated balance.
    request = request_history[1]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '7'
    assert request.headers['RDN-Balance-Signature']

    # Third cycle, adapt new balance and pay price again.
    request = request_history[2]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '10'

    assert session.channel.balance == 10
    balance_sig_hex = encode_hex(session.channel.balance_sig)
    assert request.headers['RDN-Balance-Signature'] == balance_sig_hex
    assert session.channel.balance_sig
    assert response.text == 'success'


def test_full_cycle_error_500(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    session.initial_deposit = lambda x: x

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '3'

        headers2 = Munch()
        headers2.cost = '3'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 500, 'headers': {}}
        ])
        response = session.get(url)

    # Filter out any requests made to the ethereum node.
    request_history = [request for request in server_mock.request_history if request.port == 5000]

    # First cycle, request price.
    request = request_history[0]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address

    # Second cycle, pay price but receive error.
    request = request_history[1]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '3'

    assert session.channel.balance == 3
    balance_sig_hex = encode_hex(session.channel.balance_sig)
    assert request.headers['RDN-Balance-Signature'] == balance_sig_hex
    assert response.status_code == 500


def test_full_cycle_success_post(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    session.initial_deposit = lambda x: x

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '7'

        headers2 = Munch()
        headers2.cost = '7'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.post(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 200, 'headers': headers2, 'text': 'success'}
        ])
        response = session.post(url, json={'somefield': 'somevalue'})

    # Filter out any requests made to the ethereum node.
    request_history = [request for request in server_mock.request_history if request.port == 5000]

    # First cycle, request price.
    request = request_history[0]
    assert request.path == '/something'
    assert request.method == 'POST'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.json()['somefield'] == 'somevalue'

    # Second cycle, pay price.
    request = request_history[1]
    assert request.path == '/something'
    assert request.method == 'POST'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '7'
    assert request.json()['somefield'] == 'somevalue'

    assert session.channel.balance == 7
    balance_sig_hex = encode_hex(session.channel.balance_sig)
    assert request.headers['RDN-Balance-Signature'] == balance_sig_hex
    assert session.channel.balance_sig
    assert response.text == 'success'


def test_custom_headers(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    session.initial_deposit = lambda x: x

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '7'

        headers2 = Munch()
        headers2.cost = '7'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 200, 'headers': headers2, 'text': 'success'}
        ])
        response = session.get(url, headers={
            'someheader': 'somevalue',
            # This should override the actual balance but doesn't actually make sense.
            'RDN-Balance': '5'
        })

    # Filter out any requests made to the ethereum node.
    request_history = [request for request in server_mock.request_history if request.port == 5000]

    # First cycle, request price.
    request = request_history[0]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '5'
    assert request.headers['someheader'] == 'somevalue'

    # Second cycle, pay price.
    request = request_history[1]
    assert request.path == '/something'
    assert request.method == 'GET'
    assert request.headers['RDN-Contract-Address'] == channel_manager_address
    assert request.headers['RDN-Balance'] == '5'
    assert request.headers['someheader'] == 'somevalue'

    assert session.channel.balance == 7
    balance_sig_hex = encode_hex(session.channel.balance_sig)
    assert request.headers['RDN-Balance-Signature'] == balance_sig_hex
    assert session.channel.balance_sig
    assert response.text == 'success'


def test_cheating_client(
        doggo_proxy,
        session: Session,
        http_doggo_url: str
):
    """this test scenario where client sends less funds than what is requested
        by the server. In such case, a "RDN-Invalid-Amount=1" header should
        be sent in a server's reply
    """
    def patched_payment(
            self: Session,
            method: str,
            url: str,
            response: Response,
            **kwargs
    ):
        response.headers[HTTPHeaders.PRICE] = str(
            int(response.headers[HTTPHeaders.PRICE]) + self.price_adjust
        )
        return Session.on_payment_requested(self, method, url, response, **kwargs)

    def patched_on_invalid_amount(self, method: str, url: str, response: Response, **kwargs):
        self.invalid_amount_received += 1
        price = int(response.headers[HTTPHeaders.PRICE])
        Session.on_invalid_amount(self, method, url, response, **kwargs)
        # on_invalid_amount will already prepare the next payment which we don't execute anymore,
        # so revert that.
        self.channel.update_balance(self.channel.balance - price)
        return False

    session.on_invalid_amount = types.MethodType(
        patched_on_invalid_amount,
        session
    )
    session.on_payment_requested = types.MethodType(
        patched_payment,
        session
    )

    session.invalid_amount_received = 0

    # correct amount
    session.price_adjust = 0
    response = session.get(http_doggo_url)
    check_response(response)
    assert session.invalid_amount_received == 0
    # underpay
    session.price_adjust = -1
    response = session.get(http_doggo_url)
    assert response.status_code == 402
    assert session.invalid_amount_received == 1
    # overpay
    session.price_adjust = 1
    response = session.get(http_doggo_url)
    assert response.status_code == 402
    assert session.invalid_amount_received == 2


def test_session(
        doggo_proxy,
        session: Session,
        sender_address: str,
        receiver_address: str,
        http_doggo_url: str
):
    check_response(session.get(http_doggo_url))

    client = session.client
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1

    channel = open_channels[0]
    assert channel == session.channel
    assert channel.balance_sig
    assert channel.balance < channel.deposit
    assert is_same_address(channel.sender, sender_address)
    assert is_same_address(channel.receiver, receiver_address)


def test_session_topup(
        doggo_proxy,
        session: Session,
        http_doggo_url: str
):

    # Create a channel that has just enough capacity for one transfer.
    session.initial_deposit = lambda x: 0
    check_response(session.get(http_doggo_url))

    client = session.client
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1
    channel1 = open_channels[0]
    assert channel1 == session.channel
    assert channel1.balance_sig
    assert channel1.balance == channel1.deposit

    # Do another payment. Topup should occur.
    check_response(session.get(http_doggo_url))
    open_channels = client.get_open_channels()
    assert len(open_channels) == 1
    channel2 = open_channels[0]
    assert channel2 == session.channel
    assert channel2.balance_sig
    assert channel2.balance < channel2.deposit
    assert channel1 == channel2


def test_session_close(
        doggo_proxy,
        session: Session,
        http_doggo_url: str
):
    client = session.client
    check_response(session.get(http_doggo_url))
    session.close_channel()
    open_channels = client.get_open_channels()
    assert len(open_channels) == 0


def test_session_existing_channel(
        doggo_proxy,
        session: Session,
        receiver_address: str,
        http_doggo_url: str
):
    client = session.client
    channel = client.open_channel(receiver_address, 50)
    check_response(session.get(http_doggo_url))
    assert channel.balance == 2
    assert channel.deposit == 50


def test_session_existing_channel_topup(
        doggo_proxy,
        session: Session,
        receiver_address: str,
        http_doggo_url: str
):
    client = session.client
    session.topup_deposit = lambda x: 13
    channel = client.open_channel(receiver_address, 1)
    check_response(session.get(http_doggo_url))
    assert channel.balance == 2
    assert channel.deposit == 13


def test_coop_close(
        doggo_proxy,
        session: Session,
        http_doggo_url: str
):
    check_response(session.get(http_doggo_url))

    client = session.client
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


@pytest.mark.parametrize('proxy_ssl', [1])
def test_ssl_client(
        doggo_proxy,
        session: Session,
        https_doggo_url: str
):
    with pytest.raises(SSLError):
        check_response(session.get(https_doggo_url))
    check_response(session.get(https_doggo_url, verify=False))


def test_status_codes(
        doggo_proxy,
        session: Session,
        http_doggo_url: str
):
    response = session.get(http_doggo_url)
    assert response.status_code == 200
    response = session.get(http_doggo_url[:-1])
    assert response.status_code == 404


def test_requests(
    patched_contract,
    web3: Web3,
    sender_privkey: str,
    api_endpoint_address: str,
    token_address: str,
    channel_manager_address: str,
    receiver_address: str,
    revert_chain
):
    import microraiden.requests

    with requests_mock.mock(real_http=True) as server_mock:
        headers1 = Munch()
        headers1.token_address = token_address
        headers1.contract_address = channel_manager_address
        headers1.receiver_address = receiver_address
        headers1.price = '7'

        headers2 = Munch()
        headers2.cost = '7'

        headers1 = HTTPHeaders.serialize(headers1)
        headers2 = HTTPHeaders.serialize(headers2)

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers1},
            {'status_code': 200, 'headers': headers2, 'text': 'success'}
        ])
        response = microraiden.requests.get(
            url,
            retry_interval=0.1,
            private_key=sender_privkey,
            web3=web3,
            channel_manager_address=channel_manager_address
        )

    assert response.text == 'success'


def test_cooperative_close_denied(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    cooperative_close_denied_mock = mock.patch.object(
        session,
        'on_cooperative_close_denied',
        wraps=session.on_cooperative_close_denied
    ).start()

    with requests_mock.mock(real_http=True) as server_mock:
        headers = {
            HTTPHeaders.TOKEN_ADDRESS: token_address,
            HTTPHeaders.CONTRACT_ADDRESS: channel_manager_address,
            HTTPHeaders.RECEIVER_ADDRESS: receiver_address,
            HTTPHeaders.PRICE: '3'
        }
        headers = [headers.copy() for _ in range(2)]
        headers[1][HTTPHeaders.COST] = '3'

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers[0]},
            {'status_code': 200, 'headers': headers[1], 'text': 'success'},
        ])
        channel_url = re.compile(
            'http://{}/api/1/channels/0x.{{40}}/\d+'.format(api_endpoint_address)
        )
        server_mock.delete(channel_url, [
            {'status_code': 403}
        ])
        response = session.get(url)
        session.close_channel()

    assert response.text == 'success'
    assert cooperative_close_denied_mock.call_count == 1
    assert session.channel.state == Channel.State.settling


def test_error_handling(
        session: Session,
        api_endpoint_address: str,
        token_address: str,
        channel_manager_address: str,
        receiver_address: str
):
    nonexisting_channel_mock = mock.patch.object(
        session,
        'on_nonexisting_channel',
        wraps=session.on_nonexisting_channel
    ).start()
    insufficient_confirmations_mock = mock.patch.object(
        session,
        'on_insufficient_confirmations',
        wraps=session.on_insufficient_confirmations
    ).start()
    insufficient_funds_mock = mock.patch.object(
        session,
        'on_invalid_balance_proof',
        wraps=session.on_invalid_balance_proof
    ).start()
    invalid_contract_address_mock = mock.patch.object(
        session,
        'on_invalid_contract_address',
        wraps=session.on_invalid_contract_address
    ).start()

    with requests_mock.mock(real_http=True) as server_mock:
        headers = {
            HTTPHeaders.TOKEN_ADDRESS: token_address,
            HTTPHeaders.CONTRACT_ADDRESS: channel_manager_address,
            HTTPHeaders.RECEIVER_ADDRESS: receiver_address,
            HTTPHeaders.PRICE: '3'
        }
        headers = [headers.copy() for _ in range(5)]
        headers[1][HTTPHeaders.NONEXISTING_CHANNEL] = '1'
        headers[2][HTTPHeaders.INSUF_CONFS] = '1'
        headers[3][HTTPHeaders.INVALID_PROOF] = '1'
        headers[4][HTTPHeaders.CONTRACT_ADDRESS] = '0x' + '12' * 20

        url = 'http://{}/something'.format(api_endpoint_address)
        server_mock.get(url, [
            {'status_code': 402, 'headers': headers[0]},
            {'status_code': 402, 'headers': headers[1]},
            {'status_code': 402, 'headers': headers[2]},
            {'status_code': 402, 'headers': headers[3]},
            {'status_code': 402, 'headers': headers[4]}
        ])
        response = session.get(url)

    assert response.status_code == 402
    assert nonexisting_channel_mock.call_count == 1
    assert insufficient_confirmations_mock.call_count == 1
    assert insufficient_funds_mock.call_count == 1
    assert invalid_contract_address_mock.call_count == 1

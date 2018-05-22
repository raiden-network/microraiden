from itertools import cycle

import requests
from eth_utils import encode_hex
from munch import Munch

from microraiden import HTTPHeaders, Client
from microraiden.proxy.resources import Expensive
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from flask import request, jsonify

import logging
log = logging.getLogger(__name__)


class StaticPriceResource(Expensive):
    def get(self, url):
        return 'GET'

    def post(self, url):
        return 'POST'

    def put(self, url):
        return 'PUT'

    def delete(self, url):
        return 'DEL'


class DynamicPriceResource(Expensive):
    def get(self, url, res_id: int):
        return res_id, 200


class DynamicMethodResource(StaticPriceResource):
    def __init__(self, foo, bar=12345, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert foo == 42
        assert bar == 9814072356

    def price(self):
        prices = {
            'GET': 1,
            'POST': 2,
            'PUT': 3,
            'DELETE': 4
        }
        return prices[request.method]


class TextResource(Expensive):
    def get(self, url):
        return 'GET', 200, {'Content-Type': 'text'}


class JSONResource(Expensive):
    def get(self, url):
        return jsonify({'GET': 1})


def assert_method(method, url, headers, channel, expected_reply, expected_price=3):
    # test POST
    response = method(url, headers=headers)
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == expected_price

    channel.update_balance(int(headers.sender_balance) + int(headers.price))

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = method(url, headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == expected_reply


def test_static_price(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    proxy.add_paywalled_resource(StaticPriceResource, '/resource', 3)

    # test GET
    response = requests.get(endpoint_url + '/resource')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 3

    channel = client.get_suitable_channel(headers.receiver_address, int(headers.price) * 4)
    wait_for_blocks(6)
    channel.update_balance(int(headers.price))

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource', headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == 'GET'

    assert_method(requests.post, endpoint_url + '/resource', headers, channel, 'POST')
    assert_method(requests.put, endpoint_url + '/resource', headers, channel, 'PUT')
    assert_method(requests.delete, endpoint_url + '/resource', headers, channel, 'DEL')


def test_dynamic_price(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    price_cycle = cycle([1, 2, 3, 4, 5])
    url_to_price = {}  # type: Dict

    def price_fn():
        url = request.path
        if int(url.split('_')[-1]) == 0:
            return 0
        if url in url_to_price:
            price = url_to_price[url]
        else:
            price = next(price_cycle)
            url_to_price[url] = price
        return price

    proxy.add_paywalled_resource(
        DynamicPriceResource,
        '/resource_<int:res_id>',
        price=price_fn
    )

    response = requests.get(endpoint_url + '/resource_3')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 1

    response = requests.get(endpoint_url + '/resource_5')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 2

    response = requests.get(endpoint_url + '/resource_2')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 3

    response = requests.get(endpoint_url + '/resource_3')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 1

    response = requests.get(endpoint_url + '/resource_0')
    assert response.status_code == 200
    assert response.text.strip() == '0'

    channel = client.get_suitable_channel(headers.receiver_address, 2)
    wait_for_blocks(6)
    channel.update_balance(2)

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource_5', headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == '5'


def test_method_price(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    proxy.add_paywalled_resource(
        DynamicMethodResource,
        '/resource',
        resource_class_args=(42,),
        resource_class_kwargs={'bar': 9814072356})

    # test GET
    response = requests.get(endpoint_url + '/resource')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 1

    channel = client.get_suitable_channel(headers.receiver_address, 1 + 2 + 3 + 4)
    wait_for_blocks(6)
    channel.update_balance(int(headers.price))

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource', headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == 'GET'

    assert_method(requests.post,
                  endpoint_url + '/resource',
                  headers, channel, 'POST',
                  expected_price=2)
    assert_method(requests.put,
                  endpoint_url + '/resource',
                  headers, channel, 'PUT',
                  expected_price=3)
    assert_method(requests.delete,
                  endpoint_url + '/resource',
                  headers, channel, 'DEL',
                  expected_price=4)


def test_text(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    proxy.add_paywalled_resource(TextResource, '/resource', 3)

    # test GET
    response = requests.get(endpoint_url + '/resource')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 3

    channel = client.get_suitable_channel(headers.receiver_address, int(headers.price) * 4)
    wait_for_blocks(6)
    channel.update_balance(int(headers.price))

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource', headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text'
    assert response.text == 'GET'


def test_explicit_json(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    proxy.add_paywalled_resource(JSONResource, '/resource', 3)

    # test GET
    response = requests.get(endpoint_url + '/resource')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 3

    channel = client.get_suitable_channel(headers.receiver_address, int(headers.price) * 4)
    wait_for_blocks(6)
    channel.update_balance(int(headers.price))

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource', headers=headers)
    assert response.status_code == 200
    # If headers don't merge properly, this results in 'application/json,application/json'.
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'GET': 1}

from itertools import cycle

import requests
from eth_utils import encode_hex
from munch import Munch

from microraiden import HTTPHeaders, Client
from microraiden.proxy.content import PaywalledContent
from microraiden.proxy.paywalled_proxy import PaywalledProxy


def test_static_price(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    content = PaywalledContent(
        'resource', price=3, get_fn=lambda url: ('SUCCESS', 200),
    )
    proxy.add_content(content)

    response = requests.get(endpoint_url + '/resource')
    assert response.status_code == 402
    headers = HTTPHeaders.deserialize(response.headers)
    assert int(headers.price) == 3

    channel = client.get_suitable_channel(headers.receiver_address, 3)
    wait_for_blocks(6)
    channel.balance = 3

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource', headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == '"SUCCESS"'


def test_dynamic_price(
        empty_proxy: PaywalledProxy,
        api_endpoint_address: str,
        client: Client,
        wait_for_blocks
):
    proxy = empty_proxy
    endpoint_url = "http://" + api_endpoint_address

    price_cycle = cycle([1, 2, 3, 4, 5])
    url_to_price = {}

    def price_fn(url: str):
        if url in url_to_price:
            price = url_to_price[url]
        else:
            price = next(price_cycle)
            url_to_price[url] = price
        return price

    content = PaywalledContent(
        'resource_\d', price=price_fn, get_fn=lambda url: (url.split("_")[1], 200),
    )
    proxy.add_content(content)

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

    channel = client.get_suitable_channel(headers.receiver_address, 2)
    wait_for_blocks(6)
    channel.balance = 2

    headers = Munch()
    headers.balance = str(channel.balance)
    headers.balance_signature = encode_hex(channel.balance_sig)
    headers.sender_address = channel.sender
    headers.open_block = str(channel.block)
    headers = HTTPHeaders.serialize(headers)

    response = requests.get(endpoint_url + '/resource_5', headers=headers)
    assert response.status_code == 200
    assert response.text.strip() == '"5"'

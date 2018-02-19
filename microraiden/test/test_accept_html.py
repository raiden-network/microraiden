import requests
from microraiden import HTTPHeaders as header


def test_accept_html(doggo_proxy, api_endpoint_address, wait_for_blocks):
    endpoint_url = "http://" + api_endpoint_address
    wait_for_blocks(1)

    headers = {
        'Accept': 'text/html'
    }
    rv = requests.get(endpoint_url + "/doggo.jpg", headers=headers)
    assert 'Content-Type' in rv.headers
    assert header.RECEIVER_ADDRESS in rv.headers
    assert header.CONTRACT_ADDRESS in rv.headers
    assert header.GATEWAY_PATH in rv.headers
    assert header.PRICE in rv.headers
    assert rv.headers['Content-Type'] == headers['Accept']
    assert rv.status_code == 402
    assert '<html' in rv.text


def test_accept_json(doggo_proxy, api_endpoint_address, wait_for_blocks):
    # default mode is to receive application/json
    endpoint_url = "http://" + api_endpoint_address
    wait_for_blocks(1)
    rv = requests.get(endpoint_url + "/doggo.jpg")
    assert 'Content-Type' in rv.headers
    assert header.RECEIVER_ADDRESS in rv.headers
    assert header.CONTRACT_ADDRESS in rv.headers
    assert header.GATEWAY_PATH in rv.headers
    assert header.PRICE in rv.headers
    assert rv.headers['Content-Type'] == 'application/json'
    assert rv.status_code == 402
    assert '<html' not in rv.text

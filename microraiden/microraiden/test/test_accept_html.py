import requests


def test_accept_html(doggo_proxy, api_endpoint_address, wait_for_blocks):
    endpoint_url = "http://" + api_endpoint_address
    wait_for_blocks(1)

    headers = {
        'Accept': 'text/html'
    }
    rv = requests.get(endpoint_url + "/doggo.jpg", headers=headers)
    assert rv.status_code == 402
    assert '<html' in rv.text

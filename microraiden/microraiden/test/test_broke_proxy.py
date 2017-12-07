from microraiden import DefaultHTTPClient
from microraiden.test.utils.client import patch_on_http_response

from microraiden.test.config import (
    FAUCET_ADDRESS,
)


#  @pytest.mark.skip(reason="waiting for client to return status code")
def test_cheating_client(
        doggo_proxy,
        web3,
        default_http_client: DefaultHTTPClient,
        wait_for_blocks,
        http_doggo_url: str,
):
    patch_on_http_response(default_http_client, abort_on=[502])
    balance = web3.eth.getBalance(doggo_proxy.channel_manager.receiver)
    assert balance > 0
    # remove all receiver's eth
    web3.eth.sendTransaction({'from': doggo_proxy.channel_manager.receiver,
                              'to': FAUCET_ADDRESS,
                              'value': balance - 90000})
    wait_for_blocks(1)
    default_http_client.get(http_doggo_url)
    # proxy is expected to return 502 - it has no funds
    assert default_http_client.last_response.status_code == 502
    web3.eth.sendTransaction({'from': FAUCET_ADDRESS,
                              'to': doggo_proxy.channel_manager.receiver,
                              'value': balance})
    wait_for_blocks(1)
    default_http_client.get(http_doggo_url)
    # now it should proceed normally
    assert default_http_client.last_response.status_code == 200

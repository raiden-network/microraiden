from microraiden import Session


def test_cheating_client(
        doggo_proxy,
        web3,
        session: Session,
        wait_for_blocks,
        http_doggo_url: str,
        faucet_address: str
):
    balance = web3.eth.getBalance(doggo_proxy.channel_manager.receiver)
    assert balance > 0
    # remove all receiver's eth
    web3.eth.sendTransaction({'from': doggo_proxy.channel_manager.receiver,
                              'to': faucet_address,
                              'value': balance - 4 * 10**7})
    wait_for_blocks(1)
    response = session.get(http_doggo_url)
    # proxy is expected to return 502 - it has no funds
    assert response.status_code == 502
    web3.eth.sendTransaction({'from': faucet_address,
                              'to': doggo_proxy.channel_manager.receiver,
                              'value': balance})
    wait_for_blocks(1)
    response = session.get(http_doggo_url)
    # now it should proceed normally
    assert response.status_code == 200

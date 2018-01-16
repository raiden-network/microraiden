from microraiden import Session
from microraiden.config import NETWORK_CFG
from microraiden.utils import create_signed_transaction


def test_cheating_client(
        doggo_proxy,
        web3,
        session: Session,
        wait_for_transaction,
        http_doggo_url: str,
        faucet_private_key: str,
        faucet_address: str,
        receiver_privkey: str,
        receiver_address: str
):
    balance = web3.eth.getBalance(doggo_proxy.channel_manager.receiver)
    assert balance > 0
    # remove all receiver's eth
    tx = create_signed_transaction(
        receiver_privkey,
        web3,
        faucet_address,
        balance - NETWORK_CFG.GAS_PRICE * NETWORK_CFG.POT_GAS_LIMIT
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)
    response = session.get(http_doggo_url)
    # proxy is expected to return 502 - it has no funds
    assert response.status_code == 502
    tx = create_signed_transaction(
        faucet_private_key,
        web3,
        receiver_address,
        balance - NETWORK_CFG.GAS_PRICE * NETWORK_CFG.POT_GAS_LIMIT
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)
    response = session.get(http_doggo_url)
    # now it should proceed normally
    assert response.status_code == 200

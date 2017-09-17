import filelock
import pytest

from microraiden import Client
from microraiden.client import Channel
from microraiden.crypto import sign_balance_proof
from microraiden.test.utils.client import close_channel_cooperatively


def test_client(client: Client, receiver_privkey, receiver_address):
    """test if contract calls go through"""

    import logging
    logging.basicConfig(level=logging.INFO)

    c = client.open_channel(receiver_address, 10)
    assert c is not None

    sig = c.create_transfer(5)
    assert sig is not None

    ev = c.topup(10)
    assert ev is not None
    assert c.deposit == 20

    ev = c.close()
    assert ev is not None

    close_channel_cooperatively(c, receiver_privkey)


def test_cooperative_close(client: Client, receiver_privkey, receiver_address):
    c = client.get_suitable_channel(receiver_address, 3)
    c.create_transfer(3)

    assert c.deposit >= 3
    assert c.balance == 3

    sig = sign_balance_proof(receiver_privkey, c.receiver, c.block, c.balance)
    assert c.close_cooperatively(sig)
    assert c.state == Channel.State.closed


def test_integrity(client: Client, receiver_address):
    c = client.get_suitable_channel(receiver_address, 5)
    assert c.balance == 0
    assert c.balance_sig == sign_balance_proof(client.privkey, receiver_address, c.block, 0)
    assert c.is_valid()

    # Balance update without sig update.
    c._balance = 2
    assert not c.is_valid()

    # Proper balance update with sig update.
    c.balance = 2
    assert c.is_valid()

    # Random sig.
    c._balance_sig = b'wrong'
    assert not c.is_valid()

    # Balance exceeds deposit.
    c.balance = 100
    assert not c.is_valid()


def test_filelock(
        sender_privkey,
        client_contract_proxy,
        client_token_proxy,
        datadir,
        channel_manager_contract_address,
        token_contract_address
):
    kwargs = {
        'privkey': sender_privkey,
        'channel_manager_proxy': client_contract_proxy,
        'token_proxy': client_token_proxy,
        'datadir': datadir,
        'channel_manager_address': channel_manager_contract_address,
        'token_address': token_contract_address
    }
    client = Client(**kwargs)
    client.close()

    client = Client(**kwargs)
    with pytest.raises(filelock.Timeout):
        Client(**kwargs)
    client.close()

    with Client(**kwargs):
        pass

    with Client(**kwargs):
        with pytest.raises(filelock.Timeout):
            Client(**kwargs)

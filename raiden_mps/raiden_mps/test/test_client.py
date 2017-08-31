import pytest

from raiden_mps import Client
from raiden_mps.client import Channel
from raiden_mps.crypto import sign_balance_proof


def test_client(client: Client, receiver_address, clean_channels):
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


def test_cooperative_close(client: Client, receiver_privkey, receiver_address, clean_channels):
    c = client.get_suitable_channel(receiver_address, 3)
    c.create_transfer(3)

    assert c.deposit >= 3
    assert c.balance == 3

    sig = sign_balance_proof(receiver_privkey, c.receiver, c.block, c.balance)
    assert c.close_cooperatively(sig)
    assert c.state == Channel.State.closed

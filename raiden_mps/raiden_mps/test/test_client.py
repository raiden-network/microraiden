import pytest

from raiden_mps import Client


def test_client(client: Client, receiver_address, clean_channels,
                token_contract_address, channel_manager_contract_address):
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

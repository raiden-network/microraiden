import pytest

from raiden_mps import RMPClient
from raiden_mps.config import TOKEN_ADDRESS, TEST_SENDER_PRIVKEY
from raiden_mps.test.utils.client import close_all_channels_cooperatively


@pytest.mark.parametrize('token_contract_address', [TOKEN_ADDRESS])
@pytest.mark.parametrize('sender_privkey', [TEST_SENDER_PRIVKEY])
def test_client(rmp_client: RMPClient, receiver_address):
    """test if contract calls go through"""

    import logging
    logging.basicConfig(level=logging.INFO)

    close_all_channels_cooperatively(rmp_client, balance=0)

    c = rmp_client.open_channel(receiver_address, 10)
    assert c is not None

    sig = c.create_transfer(5)
    assert sig is not None

    ev = c.topup(10)
    assert ev is not None
    assert c.deposit == 20

    ev = c.close()
    assert ev is not None

    close_all_channels_cooperatively(rmp_client, balance=0)

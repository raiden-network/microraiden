import pytest

from raiden_mps.config import TOKEN_ADDRESS, TEST_SENDER_PRIVKEY


@pytest.mark.parametrize('token_contract_address', [TOKEN_ADDRESS])
@pytest.mark.parametrize('sender_privkey', [TEST_SENDER_PRIVKEY])
def test_client(rmp_client, receiver_address):
    """test if contract calls go through"""

    import logging
    logging.basicConfig(level=logging.INFO)

    c = rmp_client.open_channel(receiver_address, 10)
    assert c is not None

    sig = c.create_transfer(5)
    assert sig is not None

    ev = c.topup(10)
    assert ev is not None
    assert c.deposit == 20

    ev = c.close()
    assert ev is not None


def test_m2m_client(doggo_proxy, m2m_client):
    x = m2m_client.request_resource('doggo.jpg')
    assert x.decode().strip() == '"HI I AM A DOGGO"'

import pytest


@pytest.mark.parametrize('token_contract_address', ['0x54f181ab7c8ff2feb4a0f996401fbbf75fd94ae4'])
@pytest.mark.parametrize('sender_privkey',
                         ['aef33c9f83550b526672e550ffaf3eae91869b54ae871248e8e9c0cffb641d82'])
def test_client(rmp_client, receiver_address):
    """test if contract calls go through"""
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

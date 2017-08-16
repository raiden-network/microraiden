import pytest


def test_client(rmp_client, receiver_address):
    """test if contract calls go through"""
    c = rmp_client.open_channel(receiver_address, 10)
    assert c is not None

    sig = rmp_client.create_transfer(c, 5)
    assert sig is not None

    ev = rmp_client.topup_channel(c, 10)
    assert ev is not None
    assert c.deposit == 20

    ev = rmp_client.close_channel(c)
    assert ev is not None

def test_m2m_client(doggo_proxy, m2m_client):
    x = m2m_client.request_resource('doggo.jpg')
    assert x.decode().strip() == '"HI I AM A DOGGO"'

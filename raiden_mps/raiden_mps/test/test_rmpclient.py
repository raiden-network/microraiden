import pytest


@pytest.fixture
def receiver_address():
    return '0x004b52c58863c903ab012537247b963c557929e8'


def test_client(rmp_client, receiver_address):
    c = rmp_client.open_channel(receiver_address, 10)
    assert c is not None

    sig = rmp_client.create_transfer(c, 5)
    assert sig is not None

    ev = rmp_client.topup_channel(c, 10)
    assert ev is not None
    assert c.deposit == 20

    ev = rmp_client.close_channel(c)
    assert ev is not None

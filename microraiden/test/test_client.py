import pytest
from _pytest.monkeypatch import MonkeyPatch
from py._path.local import LocalPath
from web3 import Web3

from microraiden import Client
from microraiden.client import Channel
from microraiden.utils import sign_balance_proof, sign_close
from microraiden.test.utils.client import close_channel_cooperatively
import microraiden.utils.private_key


def test_client(client: Client, receiver_address):
    """test if contract calls go through"""

    c = client.open_channel(receiver_address, 10)
    assert c is not None

    sig = c.create_transfer(5)
    assert sig is not None

    ev = c.topup(10)
    assert ev is not None
    assert c.deposit == 20

    ev = c.close()
    assert ev is not None


def test_cooperative_close(client: Client, receiver_privkey, receiver_address):
    c = client.get_suitable_channel(receiver_address, 3)
    assert c is not None
    c.create_transfer(3)

    assert c.deposit >= 3
    assert c.balance == 3

    sig = sign_close(
        receiver_privkey,
        c.sender,
        c.block,
        c.balance,
        client.context.channel_manager.address
    )
    assert c.close_cooperatively(sig)
    assert c.state == Channel.State.closed


def test_integrity(client: Client, receiver_address):
    c = client.get_suitable_channel(receiver_address, 5)
    assert c is not None
    assert c.balance == 0
    assert c.balance_sig == sign_balance_proof(
        client.context.private_key,
        receiver_address,
        c.block,
        0,
        client.context.channel_manager.address
    )
    assert c.is_valid()

    # Balance update without sig update.
    c._balance = 2
    assert not c.is_valid()

    # Proper balance update with sig update.
    c.update_balance(2)
    assert c.is_valid()

    # Random sig.
    c._balance_sig = b'wrong'
    assert not c.is_valid()

    # Balance exceeds deposit.
    c.update_balance(100)
    assert not c.is_valid()

    c.update_balance(0)


def test_sync(client: Client, receiver_address, receiver_privkey):
    c = client.get_suitable_channel(receiver_address, 5, initial_deposit=lambda x: x)
    assert c is not None
    assert c in client.channels
    assert c.deposit == 5
    assert len(client.channels) == 1

    # Check if channel is still valid after sync.
    client.sync_channels()
    assert c in client.channels
    assert len(client.channels) == 1

    # Check if client handles topup events on sync.
    c_topup = client.get_suitable_channel(receiver_address, 7, topup_deposit=lambda x: 2)
    assert c is not None
    assert c_topup == c
    assert len(client.channels) == 1
    assert c.deposit == 7

    # Check if channel can be resynced after data loss.
    client.channels = []
    client.sync_channels()
    assert len(client.channels) == 1
    c = client.channels[0]
    assert c.deposit == 7

    # Check if channel is forgotten on resync after closure.
    close_channel_cooperatively(c, receiver_privkey, client.context.channel_manager.address)

    client.sync_channels()
    assert c not in client.channels


def test_open_channel_insufficient_tokens(client: Client, web3: Web3, receiver_address: str):
    balance_of = client.context.token.call().balanceOf(client.context.address)
    tx_count_pre = web3.eth.getTransactionCount(client.context.address)
    channel = client.open_channel(receiver_address, balance_of + 1)
    tx_count_post = web3.eth.getTransactionCount(client.context.address)
    assert channel is None
    assert tx_count_post == tx_count_pre


def test_topup_channel_insufficient_tokens(client: Client, web3: Web3, receiver_address: str):
    balance_of = client.context.token.call().balanceOf(client.context.address)
    channel = client.open_channel(receiver_address, 1)
    assert channel is not None

    tx_count_pre = web3.eth.getTransactionCount(client.context.address)
    assert channel.topup(balance_of) is None
    tx_count_post = web3.eth.getTransactionCount(client.context.address)
    assert tx_count_post == tx_count_pre


def test_client_private_key_path(
        patched_contract,
        monkeypatch: MonkeyPatch,
        sender_privkey: str,
        tmpdir: LocalPath,
        web3: Web3,
        channel_manager_address: str
):
    def check_permission_safety_patched(path: str):
        return True

    monkeypatch.setattr(
        microraiden.utils.private_key,
        'check_permission_safety',
        check_permission_safety_patched
    )

    privkey_file = tmpdir.join('private_key.txt')
    privkey_file.write(sender_privkey)

    with pytest.raises(AssertionError):
        Client(
            private_key='0xthis_is_not_a_private_key',
            channel_manager_address=channel_manager_address,
            web3=web3
        )

    with pytest.raises(AssertionError):
        Client(
            private_key='0xcorrect_length_but_still_not_a_private_key_12345678901234567',
            channel_manager_address=channel_manager_address,
            web3=web3
        )

    with pytest.raises(AssertionError):
        Client(
            private_key='/nonexisting/path',
            channel_manager_address=channel_manager_address,
            web3=web3
        )

    Client(
        private_key=sender_privkey,
        channel_manager_address=channel_manager_address,
        web3=web3
    )

    Client(
        private_key=sender_privkey[2:],
        channel_manager_address=channel_manager_address,
        web3=web3
    )

    Client(
        private_key=str(tmpdir.join('private_key.txt')),
        channel_manager_address=channel_manager_address,
        web3=web3
    )

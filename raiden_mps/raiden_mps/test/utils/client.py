from raiden_mps.client import Channel
from raiden_mps import Client
from raiden_mps.config import TEST_RECEIVER_PRIVKEY
from raiden_mps.crypto import sign_close, privkey_to_addr


def close_all_channels(client: Client):
    close_events = [c.close() for c in client.channels if c.state == Channel.State.open]
    assert all(close_events)


def close_channel_cooperatively(
        channel, privkey_receiver: str=TEST_RECEIVER_PRIVKEY, balance: int=None
):
    if balance is not None:
        channel.balance = 0
        channel.state = Channel.State.open  # for settling channels
        channel.create_transfer(balance)

    closing_sig = sign_close(privkey_receiver, channel.balance_sig)
    assert (channel.close_cooperatively(closing_sig))


def close_all_channels_cooperatively(
        client: Client, privkey_receiver: str=TEST_RECEIVER_PRIVKEY, balance: int=None
):
    receiver_addr = privkey_to_addr(privkey_receiver)
    channels = [
        c for c in client.channels if c.state != Channel.State.closed and
                                      c.receiver == receiver_addr
    ]
    for channel in channels:
        close_channel_cooperatively(channel, privkey_receiver, balance)

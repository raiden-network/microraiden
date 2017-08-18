from raiden_mps.client.channel import Channel
from raiden_mps.client.rmp_client import RMPClient
from raiden_mps.crypto import sign_close, privkey_to_addr


def close_all_channels(client: RMPClient):
    close_events = [c.close() for c in client.channels if c.state == Channel.State.open]
    assert all(close_events)


def close_all_channels_cooperatively(client: RMPClient, privkey_receiver: str, balance=None):
    receiver_addr = privkey_to_addr(privkey_receiver)
    channels = [
        c for c in client.channels if c.state != Channel.State.closed and
                                      c.receiver == receiver_addr
    ]
    for channel in channels:
        if balance is not None:
            channel.balance = 0
            channel.state = Channel.State.open  # for settling channels
            channel.create_transfer(balance)

        closing_sig = sign_close(privkey_receiver, channel.balance_sig)
        assert (channel.close_cooperatively(closing_sig))

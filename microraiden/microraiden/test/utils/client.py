import types

from eth_utils import is_same_address
from requests import Response

from microraiden.client import Channel
from microraiden import Client, DefaultHTTPClient
from microraiden.utils import privkey_to_addr, sign_close


def close_all_channels(client: Client):
    close_events = [c.close() for c in client.channels if c.state == Channel.State.open]
    assert all(close_events)


def close_channel_cooperatively(
        channel: Channel, privkey_receiver: str, balance: int=None
):
    if balance is not None:
        channel.update_balance(balance)
    closing_sig = sign_close(privkey_receiver, channel.balance_sig)
    assert channel.close_cooperatively(closing_sig)


def close_all_channels_cooperatively(
        client: Client, privkey_receiver: str, balance: int=None
):
    receiver_addr = privkey_to_addr(privkey_receiver)
    client.sync_channels()
    channels = [
        c for c in client.channels
        if c.state != Channel.State.closed and is_same_address(c.receiver, receiver_addr)
    ]
    for channel in channels:
        close_channel_cooperatively(channel, privkey_receiver, balance)


def patch_on_http_response(default_http_client: DefaultHTTPClient, abort_on=[]):
    def patched(self, method: str, url: str, response: Response, **kwargs):
        self.last_response = response
        return (response.status_code not in abort_on)
    default_http_client.on_http_response = types.MethodType(
        patched,
        default_http_client
    )

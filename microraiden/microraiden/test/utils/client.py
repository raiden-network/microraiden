import logging
from typing import List

from eth_utils import to_checksum_address

from microraiden.client import Channel
from microraiden import Client
from microraiden.utils import privkey_to_addr, sign_close


log = logging.getLogger(__name__)


def close_all_channels(client: Client):
    close_events = [c.close() for c in client.channels if c.state == Channel.State.open]
    assert all(close_events)


def close_channel_cooperatively(
        channel: Channel, privkey_receiver: str, contract_address: str, balance: int=None
):
    if balance is not None:
        channel.update_balance(balance)
    closing_sig = sign_close(
        privkey_receiver,
        channel.sender,
        channel.block,
        channel.balance,
        contract_address
    )
    assert channel.close_cooperatively(closing_sig)


def close_all_channels_cooperatively(
        client: Client, private_keys: List[str], contract_address: str, balance: int=None
):
    addresses_to_keys = {
        to_checksum_address(privkey_to_addr(private_key)): private_key
        for private_key in private_keys
    }
    client.sync_channels()
    closable_channels = [c for c in client.channels if c.state != Channel.State.closed]
    log.info('Closing {} channels.'.format(len(closable_channels)))
    for channel in closable_channels:
        private_key = addresses_to_keys.get(to_checksum_address(channel.receiver))
        if private_key is not None:
            close_channel_cooperatively(channel, private_key, contract_address, balance)

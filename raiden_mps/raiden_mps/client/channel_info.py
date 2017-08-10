import json
from enum import Enum

from ethereum.utils import encode_hex, decode_hex


class ChannelInfo:
    class State(Enum):
        open = 1
        settling = 2
        closed = 3

    def __init__(self, sender, receiver, deposit, block, balance=0, balance_sig=None, state=State.open):
        self.sender = sender.lower()
        self.receiver = receiver.lower()
        self.deposit = deposit
        self.block = block
        self.balance = balance
        self.balance_sig = balance_sig
        self.state = state

    @staticmethod
    def from_json(json_file):
        channels_raw = json.load(json_file)
        for channel_raw in channels_raw:
            channel_raw['state'] = ChannelInfo.State[channel_raw['state']]
            channel_raw['balance_sig'] = decode_hex(channel_raw['balance_sig']) if channel_raw['balance_sig'] else None
        return [ChannelInfo(**channel_raw) for channel_raw in channels_raw]

    @staticmethod
    def to_json(channels, json_file):
        def serialize(o):
            if isinstance(o, bytes):
                return encode_hex(o)
            elif isinstance(o, ChannelInfo.State):
                return o.name
            else:
                return o.__dict__

        json.dump(channels, json_file, default=serialize, sort_keys=True, indent=4)

    @staticmethod
    def from_event(event, state):
        if state == ChannelInfo.State.open:
            return ChannelInfo(
                event['args']['_sender'],
                event['args']['_receiver'],
                event['args']['_deposit'],
                event['blockNumber'],
                0,
                None,
                state
            )
        elif state == ChannelInfo.State.settling:
            return ChannelInfo(
                event['args']['_sender'],
                event['args']['_receiver'],
                0,
                event['args']['_open_block_number'],
                event['args']['_balance'],
                None,
                state
            )
        elif state == ChannelInfo.State.closed:
            return ChannelInfo(
                event['args']['_sender'],
                event['args']['_receiver'],
                0,
                event['args']['_open_block_number'],
                0,
                None,
                state
            )

    @staticmethod
    def merge_infos(stored, created, settling, closed):
        channel_id_to_channel = {
            (c.sender, c.receiver, c.block): ChannelInfo(c.sender, c.receiver, 0, c.block)
            for group in (stored, created, settling, closed) for c in group
        }
        for c in stored:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.deposit = c.deposit
            c_merged.balance = c.balance
            c_merged.balance_sig = c.balance_sig
            c_merged.state = c.state

        for c in created:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.deposit = c.deposit
            c_merged.state = c.state

        for c in settling:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.state = c.state

        for c in closed:
            del channel_id_to_channel[(c.sender, c.receiver, c.block)]

        return list(channel_id_to_channel.values())
from enum import Enum
from ethereum.utils import encode_hex, decode_hex

if isinstance(encode_hex(b''), bytes):
    _encode_hex = encode_hex
    encode_hex = lambda b: _encode_hex(b).decode()


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
    def deserialize(channels_raw):
        for channel_raw in channels_raw:
            channel_raw['state'] = ChannelInfo.State[channel_raw['state']]
            channel_raw['balance_sig'] = decode_hex(channel_raw['balance_sig']) if channel_raw['balance_sig'] else None
        return [ChannelInfo(**channel_raw) for channel_raw in channels_raw]

    @staticmethod
    def serialize(channels):
        channels_raw = []
        for channel in channels:
            channel_raw = channel.__dict__.copy()
            channel_raw['state'] = channel.state.name
            channel_raw['balance_sig'] = encode_hex(channel.balance_sig) if channel.balance_sig else None
            channels_raw.append(channel_raw)

        return channels_raw

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
    def merge_infos(stored, created, settling, closed, toppedup):
        channel_id_to_channel = {
            (c.sender, c.receiver, c.block): ChannelInfo(c.sender, c.receiver, 0, c.block)
            for group in (stored, created, settling, closed, toppedup) for c in group
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

        for c in toppedup:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.deposit = max(c_merged.deposit, c.deposit)

        for c in settling:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.state = c.state

        for c in closed:
            c_merged = channel_id_to_channel[(c.sender, c.receiver, c.block)]
            c_merged.state = c.state

        return list(channel_id_to_channel.values())

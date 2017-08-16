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

    def __init__(
            self, sender, receiver, deposit, block, balance=0, balance_sig=None, state=State.open
    ):
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
            if channel_raw['balance_sig']:
                channel_raw['balance_sig'] = decode_hex(channel_raw['balance_sig'])
        return [ChannelInfo(**channel_raw) for channel_raw in channels_raw]

    @staticmethod
    def serialize(channels):
        channels_raw = []
        for channel in channels:
            channel_raw = channel.__dict__.copy()
            channel_raw['state'] = channel.state.name
            if channel.balance_sig:
                channel_raw['balance_sig'] = encode_hex(channel.balance_sig)
            else:
                channel_raw['balance_sig'] = None
            channels_raw.append(channel_raw)

        return channels_raw

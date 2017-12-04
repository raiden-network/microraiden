import time
from enum import IntEnum


class ChannelState(IntEnum):
    OPEN = 0
    CLOSED = 1
    CLOSE_PENDING = 2
    UNDEFINED = 100


class Channel(object):
    """A channel between two parties."""

    def __init__(self, receiver, sender, deposit, open_block_number):
        self.receiver = receiver
        self.sender = sender  # sender address
        self.deposit = deposit  # deposit is maximum funds that can be used
        self.open_block_number = open_block_number

        self.balance = 0  # how much of the deposit has been spent
        self.state = ChannelState.UNDEFINED
        self.last_signature = None
        # if set, this is the absolute block_number the channel can be settled
        self.settle_timeout = -1
        self.ctime = time.time()  # channel creation time
        self.mtime = self.ctime
        self.confirmed = False

        self.unconfirmed_topups = {}  # txhash to added deposit

    @property
    def is_closed(self):
        return (self.state) in (ChannelState.CLOSED, ChannelState.CLOSE_PENDING)

    @is_closed.setter
    def is_closed(self, value):
        assert value is True
        self.state = ChannelState.CLOSED

    @property
    def unconfirmed_deposit(self):
        return self.deposit + sum(self.unconfirmed_topups.values())

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, state: dict):
        ret = cls(None, None, None, None)
        assert (set(state) - set(ret.__dict__)) == set()
        for k, v in state.items():
            if k in ret.__dict__.keys():
                setattr(ret, k, v)
        return ret

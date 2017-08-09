import pytest
from rmp.channel_manager import ChannelManager

CONTRACT_ADDRESS = '0xDFC2F3Adb77Be607C8C13e68fd0Cf9242b4925f7'.lower()
RECEIVER_ADDRESS = ''
SENDER_ADDRESS = ''


@pytest.fixture
def channel_manager():
    class DummyBlockchain(object):
        def set_channel_manager(self, channel_manager):
            pass
    channel_manager = ChannelManager(DummyBlockchain(), RECEIVER_ADDRESS)
    return channel_manager


def test_channel_opening(channel_manager):
    assert SENDER_ADDRESS not in channel_manager.state.channels
    channel_manager.event_channel_opened(SENDER_ADDRESS, 100)
    assert SENDER_ADDRESS in channel_manager.state.channels
    channel = channel_manager.state.channels[SENDER_ADDRESS]
    assert channel.receiver == RECEIVER_ADDRESS
    assert channel.sender == SENDER_ADDRESS
    assert channel.deposit == 100
    assert channel.balance == 0
    assert channel.is_closed is False


def test_undisputed_channel_close(channel_manager):
    channel_manager.event_channel_opened(SENDER_ADDRESS, 100)

    def fail(*args):
        assert False
    channel_manager.close_channel = fail
    channel_manager.event_channel_close_requested(SENDER_ADDRESS, 0, 1000)
    assert SENDER_ADDRESS in channel_manager.state.channels
    channel = channel_manager.state.channels[SENDER_ADDRESS]
    assert channel.settle_timeout == 1000
    assert channel.is_closed is True

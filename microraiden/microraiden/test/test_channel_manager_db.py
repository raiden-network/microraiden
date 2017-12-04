import pytest
from microraiden.channel_manager import (
    Channel,
    ChannelState,
    ChannelManagerState
)


CONTRACT_ADDRESS = '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
RECEIVER_ADDRESS = '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
SENDER_ADDRESS = '0xcccccccccccccccccccccccccccccccccccccccc'
NETWORK_ID = 123
BLOCK_HASH = '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
SIG = '0x' + 'bb' * 130


@pytest.fixture()
def state(tmpdir):
    db = tmpdir.join("state.db")
    state = ChannelManagerState(db.strpath)
    state.setup_db(
        NETWORK_ID,
        CONTRACT_ADDRESS,
        RECEIVER_ADDRESS
    )
    return state


def test_creation(state):
    assert state.receiver == RECEIVER_ADDRESS
    assert state.contract_address == CONTRACT_ADDRESS
    assert state.network_id == NETWORK_ID

    assert state.confirmed_head_number is None
    assert state.confirmed_head_hash is None
    assert state.unconfirmed_head_number is None
    assert state.unconfirmed_head_hash is None
    assert state.n_channels == 0
    assert state.n_open_channels == 0

    state_loaded = ChannelManagerState.load(state.filename, check_permissions=False)
    assert state_loaded.confirmed_head_number is None
    assert state_loaded.confirmed_head_hash is None
    assert state_loaded.unconfirmed_head_number is None
    assert state_loaded.unconfirmed_head_hash is None
    assert state_loaded.n_channels == 0
    assert state_loaded.n_open_channels == 0


def test_sync_state(state):
    state.update_sync_state(confirmed_head_hash=BLOCK_HASH)
    assert state.confirmed_head_hash == BLOCK_HASH
    state.update_sync_state(confirmed_head_number=123)
    assert state.confirmed_head_number == 123
    state.update_sync_state(unconfirmed_head_hash=BLOCK_HASH)
    assert state.unconfirmed_head_hash == BLOCK_HASH
    state.update_sync_state(unconfirmed_head_number=321)
    assert state.unconfirmed_head_number == 321

    state_loaded = ChannelManagerState.load(state.filename, check_permissions=False)
    assert state_loaded.confirmed_head_hash == BLOCK_HASH
    assert state_loaded.confirmed_head_number == 123
    assert state_loaded.unconfirmed_head_hash == BLOCK_HASH
    assert state_loaded.unconfirmed_head_number == 321


def test_adding_channel(state):
    channel = Channel(RECEIVER_ADDRESS, SENDER_ADDRESS, 100, 123)
    channel.balance = 50
    channel.state = ChannelState.OPEN
    assert not state.channel_exists(channel.sender, channel.open_block_number)
    state.add_channel(channel)
    assert state.channel_exists(channel.sender, channel.open_block_number)
    channel_retrieved = state.get_channel(channel.sender, channel.open_block_number)
    assert channel_retrieved.sender == SENDER_ADDRESS
    assert channel_retrieved.receiver == RECEIVER_ADDRESS
    assert channel_retrieved.open_block_number == 123
    assert channel_retrieved.deposit == 100
    assert channel_retrieved.balance == 50
    assert channel_retrieved.last_signature is None
    assert channel_retrieved.is_closed is False
    assert channel_retrieved.ctime == channel.ctime
    assert channel_retrieved.mtime == channel.mtime


def test_updating_channel(state):
    channel = Channel(RECEIVER_ADDRESS, SENDER_ADDRESS, 100, 123)
    channel.balance = 50
    channel.state = ChannelState.OPEN
    state.add_channel(channel)
    channel.deposit = 200
    channel.balance = 100
    channel.last_signature = SIG
    channel.is_closed = True
    channel.mtime = channel.mtime + 1
    state.set_channel(channel)
    channel_retrieved = state.get_channel(channel.sender, channel.open_block_number)
    assert channel_retrieved.sender == SENDER_ADDRESS
    assert channel_retrieved.receiver == RECEIVER_ADDRESS
    assert channel_retrieved.open_block_number == 123
    assert channel_retrieved.deposit == 200
    assert channel_retrieved.balance == 100
    assert channel_retrieved.last_signature == SIG
    assert channel_retrieved.is_closed is True
    assert channel_retrieved.ctime == channel.ctime
    assert channel_retrieved.mtime == channel.mtime

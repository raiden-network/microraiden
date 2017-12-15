import pytest
import types
from microraiden.channel_manager import ChannelManager, Blockchain


def start_channel_manager(channel_manager, use_tester, mine_sync_event):
    if use_tester:
        mine_sync_event.clear()

        # monkeypatch Blockchain::_update() to wait for an sync event
        def update_patched(self: Blockchain):
            Blockchain._update(self)
            mine_sync_event.wait()

        channel_manager.blockchain._update = types.MethodType(
            update_patched, channel_manager.blockchain)
        # it is pointless to do busy loop as the Blockchain blocks on sync
        channel_manager.blockchain.poll_interval = 0

        def stop_patched(self: ChannelManager):
            mine_sync_event.set()
            ChannelManager.stop(self)
            self.stop = types.MethodType(ChannelManager.stop, self)

        channel_manager.stop = types.MethodType(
            stop_patched, channel_manager)

    def fail(greenlet):
        raise greenlet.exception

    channel_manager.link_exception(fail)
    channel_manager.start()
    return channel_manager


@pytest.fixture
def channel_manager(
        web3,
        receiver_privkey,
        channel_manager_contract,
        token_contract,
        use_tester,
        mine_sync_event,
        state_db_path,
        patched_contract,
        revert_chain
):
    manager = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver_privkey,
        n_confirmations=5,
        state_filename=state_db_path
    )
    start_channel_manager(manager, use_tester, mine_sync_event)
    yield manager
    manager.stop()

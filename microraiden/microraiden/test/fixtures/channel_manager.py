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

        channel_manager.stop = types.MethodType(
            stop_patched, channel_manager)

    def fail(greenlet):
        raise greenlet.exception

    channel_manager.link_exception(fail)
    channel_manager.start()
    return channel_manager


@pytest.fixture
def channel_manager(web3, receiver_privkey, make_channel_manager_proxy, token_contract, use_tester,
                    mine_sync_event, state_db_path):
    if use_tester:
        snapshot_id = web3.testing.snapshot()
    contract_proxy = make_channel_manager_proxy(receiver_privkey)
    manager = ChannelManager(web3, contract_proxy, token_contract, receiver_privkey,
                             n_confirmations=5, state_filename=state_db_path)
    start_channel_manager(manager, use_tester, mine_sync_event)
    yield manager
    manager.stop()
    if use_tester:
        web3.testing.revert(snapshot_id)
    manager.stop()

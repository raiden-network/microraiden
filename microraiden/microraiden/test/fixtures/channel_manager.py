import pytest
import types
from microraiden.channel_manager import ChannelManager, Blockchain


@pytest.fixture
def channel_managers_count():
    return 2


def start_channel_manager(channel_manager, use_tester, mine_sync_event):
    # disable logging during sync
    if use_tester:

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
#    channel_manager.wait_sync()
    return channel_manager


@pytest.fixture
def channel_managers(web3, channel_manager_contract_proxies, receiver_privkeys,
                     token_contract, use_tester, mine_sync_event):
    channel_managers = [ChannelManager(web3, proxy, token_contract, privkey, n_confirmations=5)
                        for privkey, proxy in
                        zip(receiver_privkeys, channel_manager_contract_proxies)]
    for manager in channel_managers:
        start_channel_manager(manager, use_tester, mine_sync_event)
    return channel_managers


@pytest.fixture
def channel_manager(channel_managers):
    return channel_managers[0]

import pytest
import types
from microraiden.channel_manager import ChannelManager, Blockchain

@pytest.fixture
def channel_managers_count():
    return 2


def start_channel_manager(channel_manager, use_tester, mine_sync_event):
    # disable logging during sync
#    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    if use_tester:
        x = channel_manager.blockchain._update

        def update_patched(self: Blockchain):
            x()
            mine_sync_event.wait()

        channel_manager.blockchain._update = types.MethodType(
            update_patched, channel_manager.blockchain)
        channel_manager.blockchain.poll_interval = 0

    def fail(greenlet):
        raise greenlet.exception

    channel_manager.link_exception(fail)
    channel_manager.start()
#    channel_manager.wait_sync()
#    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    return channel_manager


@pytest.fixture
def channel_managers(web3, channel_manager_contract_proxies, receiver_privkeys,
                     token_contract, use_tester, mine_sync_event):
#    logging.getLogger('channel_manager').setLevel(logging.WARNING)
    channel_managers = [ChannelManager(web3, proxy, token_contract, privkey, n_confirmations=5)
                        for privkey, proxy in
                        zip(receiver_privkeys, channel_manager_contract_proxies)]
    for manager in channel_managers:
        start_channel_manager(manager, use_tester, mine_sync_event)
    return channel_managers


@pytest.fixture
def channel_manager(channel_managers):
    return channel_managers[0]

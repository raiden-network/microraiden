import pytest
from microraiden.test.config import (
    RECEIVER_ETH_ALLOWANCE,
    RECEIVER_TOKEN_ALLOWANCE
)
from microraiden.channel_manager import ChannelManager
from microraiden.exceptions import InvalidContractVersion
from microraiden.crypto import privkey_to_addr


class FakeChannelManagerContract:
    def __init__(self, receiver1_privkey):
        self._address = privkey_to_addr(receiver1_privkey)

    def call(self):
        # forgive me God for I have sinned here
        return self

    def version(self):
        return "6.6.6"

    @property
    def address(self):
        return self._address


def test_version(web3,
                 make_channel_manager_proxy,
                 token_contract,
                 make_account):
    """Test if proxy refuses to run if it deployed contract version
    is different from the one it expects"""
    receiver1_privkey = make_account(RECEIVER_ETH_ALLOWANCE, RECEIVER_TOKEN_ALLOWANCE)
    channel_manager_contract = make_channel_manager_proxy(receiver1_privkey)

    # this one should not raise
    cm = ChannelManager(
        web3,
        channel_manager_contract,
        token_contract,
        receiver1_privkey,
        state_filename=":memory:"
    )
    cm.stop()
    # now we patch it
    channel_manager_contract.contract = FakeChannelManagerContract(receiver1_privkey)

    # check of version string should fail here
    with pytest.raises(InvalidContractVersion):
        ChannelManager(
            web3,
            channel_manager_contract,
            token_contract,
            receiver1_privkey,
            state_filename=":memory:"
        )

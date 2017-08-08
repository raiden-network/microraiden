import pytest
from server import (
    ChannelManagerState,
    ChannelManager,
    blockchain,
    contract
)
from test.utils import ChannelManagerMock
from server_flask import PaymentProxy

def testme(init_contract_address, manager_state_path):
    myaddr = "0x" + "9"*40
    app = PaymentProxy(blockchain, ChannelManager(
        myaddr, blockchain,
        state_filename=manager_state_path))

    app.run(debug=True)
    app.app.get("/")

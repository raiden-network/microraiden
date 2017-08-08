import pytest # noqa
from server import (
    blockchain,
)

from server_flask import PaymentProxy
import header


def testme(init_contract_address, manager_state_path):
    app = PaymentProxy(blockchain)
    tc = app.app.test_client()

    rv = tc.get("/expensive/something")
#    import pudb; pudb.set_trace()
    assert rv.status_code == 402

    headers = {
        header.BALANCE_SIGNATURE: "0x123456789="
    }
    rv = tc.get("/expensive/something", headers=headers)
    assert rv.status_code == 200

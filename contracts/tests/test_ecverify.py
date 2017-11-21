import pytest
from ethereum import tester
from utils import sign
from tests.fixtures import (
    create_contract
)


@pytest.fixture
def ecverify_test_contract(chain, create_contract):
    ECVerifyTest = chain.provider.get_contract_factory('ECVerifyTest')
    ecverify_test_contract = create_contract(ECVerifyTest, [])

    return ecverify_test_contract


def test_sign(web3, ecverify_test_contract):
    (A, B) = web3.eth.accounts[:2]
    message = "daddydaddycool"
    prefixed_message = sign.eth_message_prefixed(message)

    signed_message, addr = sign.check(message, tester.k0)
    signed_message_false, addr1 = sign.check(message, tester.k1)
    assert addr == A
    assert addr1 == B
    assert len(signed_message) == 65
    assert len(signed_message_false) == 65


    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(prefixed_message, bytearray())

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(prefixed_message, bytearray(64))

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(prefixed_message, bytearray(66))

    web3.testing.mine(30)
    verified_address = ecverify_test_contract.call().verify(message, signed_message)
    assert verified_address != A

    verified_address = ecverify_test_contract.call().verify(prefixed_message, signed_message)
    assert verified_address == A

    verified_address_false = ecverify_test_contract.call().verify(prefixed_message, signed_message_false)
    assert verified_address_false != A
    assert verified_address_false == B

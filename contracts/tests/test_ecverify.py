import pytest
from ethereum import tester
from utils import sign
from tests.utils import balance_proof_hash
from tests.fixtures import (
    create_contract,
    token_contract,
    channels_contract
)


@pytest.fixture
def ecverify_test_contract(chain, create_contract):
    ECVerifyTest = chain.provider.get_contract_factory('ECVerifyTest')
    ecverify_test_contract = create_contract(ECVerifyTest, [])

    return ecverify_test_contract


def test_ecrecover_output(web3, ecverify_test_contract):
    (A, B) = web3.eth.accounts[:2]
    block = 4804175
    balance = 22000000000000000000

    balance_message_hash = balance_proof_hash(B, block, balance)
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k0)
    assert addr == A

    # r = signed_message[:32];
    # s = signed_message[32:64];
    # v = int(binascii.hexlify(signed_message[64:65]), 16) # int(signed_message[64:65]);

    r = bytes.fromhex('12d99ba7bd20ac17bac65bfd646146c1ddbeb607519db6e7935684334d891ed6')
    s = bytes.fromhex('5d4ea3a13697c1d506f7bdb8cd672b944e2053d6d6bd87d4aa512fdc29ed9ae4')
    v = 28
    address = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'

    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(balance_message_hash, r, s, 0)

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(balance_message_hash, r, bytearray(), v)

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(balance_message_hash, bytearray(), s, v)

    web3.testing.mine(30)
    verified_address = ecverify_test_contract.call().verify_ecrecover_output(balance_message_hash, r, s, v)
    # assert address == verified_address


def test_sign(web3, ecverify_test_contract):
    (A, B) = web3.eth.accounts[:2]
    block = 4804175
    balance = 22000000000000000000

    balance_message_hash = balance_proof_hash(B, block, balance)
    balance_message_hash2 = balance_proof_hash(B, block, balance + 1000)
    signed_message, addr = sign.check(balance_message_hash, tester.k0)
    signed_message_false, addr1 = sign.check(balance_message_hash, tester.k1)
    assert addr == A
    assert addr1 == B
    assert len(signed_message) == 65
    assert len(signed_message_false) == 65

    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(balance_message_hash, bytearray())

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(balance_message_hash, bytearray(64))

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(balance_message_hash, bytearray(66))

    web3.testing.mine(30)
    verified_address = ecverify_test_contract.call().verify(balance_message_hash2, signed_message)
    assert verified_address != A

    verified_address = ecverify_test_contract.call().verify(balance_message_hash, signed_message)
    assert verified_address == A

    verified_address_false = ecverify_test_contract.call().verify(balance_message_hash, signed_message_false)
    assert verified_address_false != A
    assert verified_address_false == B

    signer = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'
    value = 1000
    value2 = 2000
    _address = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'

    signed_message = '0x0adc437691e266072e9aa1763329062a6b2fa1d7f94034f1b1e691218fe9fd285f4f20132fa00230f591571a3575456bb382040e02e93ff0f32544907748a9821c'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedData(_address, value, value2, signed_message)
    assert verified_address == signer


def test_verifyBalanceProof(web3, token_contract, channels_contract):
    (A, B) = web3.eth.accounts[:2]
    challenge_period = 5
    supply = 10000 * 10**18
    token = token_contract([supply, "CustomToken", "TKN", 18])
    contract = channels_contract([token.address, challenge_period])

    signer = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'
    receiver = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'
    block = 4804175
    balance = 22000000000000000000
    balance_msg_sig = '0x1803dfc1e597c08f0cc3f6e39fb109f6497c2b5321deb656f54567981889fddb49c82a33ecae2b1ae86f2fb50f0929cbad097502f8c04c7bfb8ae51883d3e1371b'
    balance_msg_sig = bytes.fromhex(balance_msg_sig[2:])

    signature_address = contract.call().verifyBalanceProof(receiver, block, balance, balance_msg_sig)
    assert signature_address == signer

    balance_message_hash = balance_proof_hash(B, block, balance)
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k0)
    assert addr == A

    signature_address = contract.call().verifyBalanceProof(B, block, balance, balance_msg_sig)
    assert signature_address == A

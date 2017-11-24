import pytest
from ethereum import tester
from utils import sign
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
    message = "daddydaddycool"
    prefixed_message = sign.eth_message_prefixed(message)
    hash_prefixed_message = sign.eth_message_hex(message)
    signed_message, addr = sign.check(message, tester.k0)

    # r = signed_message[:32];
    # s = signed_message[32:64];
    # v = int(binascii.hexlify(signed_message[64:65]), 16) # int(signed_message[64:65]);

    r = bytes.fromhex('12d99ba7bd20ac17bac65bfd646146c1ddbeb607519db6e7935684334d891ed6')
    s = bytes.fromhex('5d4ea3a13697c1d506f7bdb8cd672b944e2053d6d6bd87d4aa512fdc29ed9ae4')
    v = 28
    address = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'

    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(hash_prefixed_message, r, s, 0)

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(hash_prefixed_message, r, bytearray(), v)

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(hash_prefixed_message, bytearray(), s, v)

    web3.testing.mine(30)
    verified_address = ecverify_test_contract.call().verify_ecrecover_output(hash_prefixed_message, r, s, v)
    # assert address == verified_address


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

    signer = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'
    string_value = 'Hi, Alice!'
    value = 1000
    value2 = 2000
    _address = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'

    # Simple 1 argument string
    signed_message = '0x75b7db08c86fc75de069407b8599fd752085ff63ce52f76172d27910adda9fbf2d2f5277cc39f4dd5df52676b9428d520ac0a7c43b520c88fb42da150bad90b61b'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataString(string_value, signed_message)
    assert verified_address == signer

    # Simple 1 argument uint
    signed_message = '0x6aa4b31c2532a0e8777474393e5fadd55efabcf7af5e7b0e909c83697a92be154f5bee26c24abaf688ba3e091bb65406d5cba4168d1b7b9c0d8c7ad9b93752cc1b'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataUint(value, signed_message)
    assert verified_address == signer

    # Simple 1 argument address
    signed_message = '0x2f152a756d538855754cc4db1394bef43796d817c0a08a19ed4ea60aed20d56c09512371e74729d1ba0234853d5900c5d768cb5868212a85680eff967d3c6c6c1b'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataAddress(_address, signed_message)
    assert verified_address == signer

    # 2 arguments string, uint
    signed_message = '0xde8e36666aab7540720e7aa237f6c1d325e363bc949045b2ea8d63353858467a06c7b34a2a92bf5d4b7148b03e9b9640c13a60a03faf39bdd558ead1689899401c'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataStringUint(string_value, value, signed_message)
    assert verified_address == signer

    # 3 arguments address, string, uint
    signed_message = '0x26f649f9548f4571c754fa66a61a7116bc1d6598f00c37c40c569eb14b3656837b2e84ce4abcf2534cfb39fb680b237f9b1b5cc435b9cd3f0ed6d39af9d7011e1c'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataAddressStringUint(_address, string_value, value, signed_message)
    assert verified_address == signer

    # 3 arguments address, string, uint
    # signed_message = '0xcac6bfa507ea826309ef33d2cbbdc9a3c39d6d15479fb8f184b05abb4375539b45b45dc2ed5b710a830a26c1fe8467b989eb2a1f303a5a5c2c1971ece7c180411c'
    signed_message = '0x0adc437691e266072e9aa1763329062a6b2fa1d7f94034f1b1e691218fe9fd285f4f20132fa00230f591571a3575456bb382040e02e93ff0f32544907748a9821c'
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedDataAddressUintUint(_address, value, value2, signed_message)
    assert verified_address == signer


def test_verifyBalanceProof(web3, token_contract, channels_contract):
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

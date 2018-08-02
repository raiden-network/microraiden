import pytest
from ethereum import tester
from utils import sign
from eth_utils import encode_hex, is_same_address
from tests.utils import balance_proof_hash, closing_message_hash


@pytest.fixture
def ecverify_test_contract(chain, create_contract):
    ECVerifyTest = chain.provider.get_contract_factory('ECVerifyTest')
    ecverify_test_contract = create_contract(ECVerifyTest, [])

    return ecverify_test_contract


def test_ecrecover_output(web3, ecverify_test_contract):
    (A, B) = web3.eth.accounts[:2]
    block = 4804175
    balance = 22000000000000000000

    balance_message_hash = balance_proof_hash(B, block, balance, ecverify_test_contract.address)
    balance_msg_sig, addr = sign.check(balance_message_hash, tester.k0)
    assert is_same_address(addr, A)

    r = bytes.fromhex('12d99ba7bd20ac17bac65bfd646146c1ddbeb607519db6e7935684334d891ed6')
    s = bytes.fromhex('5d4ea3a13697c1d506f7bdb8cd672b944e2053d6d6bd87d4aa512fdc29ed9ae4')
    v = 28

    with pytest.raises(tester.TransactionFailed):
        ecverify_test_contract.call().verify_ecrecover_output(balance_message_hash, r, s, 0)

    # We have to simulate mining because ecrecover consumes a lot of gas for precompiled contracts
    # on private chains.
    web3.testing.mine(30)

    ecverify_test_contract.call().verify_ecrecover_output(
        balance_message_hash,
        r,
        s,
        v
    )


def test_sign(web3, ecverify_test_contract):
    (A, B) = web3.eth.accounts[:2]
    block = 4804175
    balance = 22000000000000000000

    balance_message_hash = balance_proof_hash(B, block, balance, ecverify_test_contract.address)
    balance_message_hash2 = balance_proof_hash(
        B,
        block,
        balance + 1000,
        ecverify_test_contract.address
    )
    signed_message, addr = sign.check(balance_message_hash, tester.k0)
    signed_message_false, addr1 = sign.check(balance_message_hash, tester.k1)
    assert is_same_address(addr, A)
    assert is_same_address(addr1, B)
    assert len(signed_message) == 65
    assert len(signed_message_false) == 65

    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(
            balance_message_hash,
            encode_hex(bytearray())
        )

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(
            balance_message_hash,
            encode_hex(bytearray(64))
        )

    web3.testing.mine(30)
    with pytest.raises(tester.TransactionFailed):
        verified_address = ecverify_test_contract.call().verify(
            balance_message_hash,
            encode_hex(bytearray(66))
        )

    web3.testing.mine(30)
    verified_address = ecverify_test_contract.call().verify(
        balance_message_hash2,
        signed_message
    )
    assert not is_same_address(verified_address, A)

    verified_address = ecverify_test_contract.call().verify(
        balance_message_hash,
        signed_message
    )
    assert is_same_address(verified_address, A)

    verified_address_false = ecverify_test_contract.call().verify(
        balance_message_hash,
        signed_message_false
    )
    assert not is_same_address(verified_address_false, A)
    assert is_same_address(verified_address_false, B)

    signer = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'
    value = 1000
    value2 = 2000
    _address = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'

    signed_message = '0x0adc437691e266072e9aa1763329062a6b2fa1d7f94034f1b1e691218fe9fd285f4f20132fa00230f591571a3575456bb382040e02e93ff0f32544907748a9821c' # noqa
    signed_message = bytes.fromhex(signed_message[2:])
    verified_address = ecverify_test_contract.call().verifyEthSignedTypedData(
        _address,
        value,
        value2,
        signed_message
    )
    assert is_same_address(verified_address, signer)


def test_extract_balance_proof_signature(get_accounts, token_instance, uraiden_instance):
    (A, B) = get_accounts(2)
    uraiden = uraiden_instance

    receiver = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'
    block = 4804175
    balance = 22000000000000000000

    message_hash = balance_proof_hash(receiver, block, balance, uraiden.address)
    balance_msg_sig, signer = sign.check(message_hash, tester.k2)
    assert is_same_address(signer, A)

    signature_address = uraiden.call().extractBalanceProofSignature(
        receiver,
        block,
        balance,
        balance_msg_sig
    )
    assert is_same_address(signature_address, signer)

    # Wrong receiver
    signature_address = uraiden.call().extractBalanceProofSignature(
        B,
        block,
        balance,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)

    # Wrong block
    signature_address = uraiden.call().extractBalanceProofSignature(
        receiver,
        10,
        balance,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)

    # Wrong balance
    signature_address = uraiden.call().extractBalanceProofSignature(
        receiver,
        block,
        20,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)


def test_extract_closing_signature(get_accounts, token_instance, uraiden_instance):
    (A, B) = get_accounts(2)
    uraiden = uraiden_instance

    sender = '0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb'
    block = 4804175
    balance = 22000000000000000000

    message_hash = closing_message_hash(sender, block, balance, uraiden.address)
    balance_msg_sig, signer = sign.check(message_hash, tester.k2)
    assert is_same_address(signer, A)

    signature_address = uraiden.call().extractClosingSignature(
        sender,
        block,
        balance,
        balance_msg_sig
    )
    assert is_same_address(signature_address, signer)

    # Wrong sender
    signature_address = uraiden.call().extractClosingSignature(
        B,
        block,
        balance,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)

    # Wrong block
    signature_address = uraiden.call().extractClosingSignature(
        sender,
        10,
        balance,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)

    # Wrong balance
    signature_address = uraiden.call().extractClosingSignature(
        sender,
        block,
        20,
        balance_msg_sig
    )
    assert not is_same_address(signature_address, signer)

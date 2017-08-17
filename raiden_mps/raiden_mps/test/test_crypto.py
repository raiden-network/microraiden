from eth_utils import force_bytes

from raiden_mps.config import CHANNEL_MANAGER_ADDRESS
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.crypto import *

SENDER_PRIVATE_KEY = 'a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0'
SENDER_ADDR = privkey_to_addr(SENDER_PRIVATE_KEY)
RECEIVER_PRIVATE_KEY = 'b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1'
RECEIVER_ADDR = privkey_to_addr(RECEIVER_PRIVATE_KEY)


def test_sha3():
    addr1 = '0x1212121212121212121212121212121212121212'
    addr2 = '0x3434343434343434343434343434343434343434'

    assert sha3_hex('a') == '3ac225168df54212a25c1c01fd35bebfea408fdac2e31ddd6f80a4bbf9a5f1cb'
    assert sha3_hex('0x0a') == '0ef9d8f8804d174666011a394cab7901679a8944d24249fd148a6a36071151f8'
    assert sha3_hex(addr1, (15, 32)) == \
        '1e17ec1733a759ef0d988fd0195d0e2792dc6181c8953130d14f9a261c6260bb'
    assert sha3_hex(addr1, (17, 32), addr2) == \
        '00424f9e17d5fecf44d798962d27cd1d44ef37d3968b05a5ff078ff696c14ea8'
    assert sha3_hex((23, 256)) == \
        'c624b66cc0138b8fabc209247f72d758e1cf3343756d543badbf24212bed8c15'
    assert sha3_hex(19) == '66de8ffda797e3de9c05e8fc57b3bf0ec28a930d40b0d285d93c06501cf6a090'
    assert sha3_hex(-5) == '7234c58e51ab4abdf62492ac6faf025ebff2afd4f861cebfa33d3e76667716a9'


def test_sign():
    msg = b'32' * 16
    assert len(msg) == 32
    sig = sign(SENDER_PRIVATE_KEY, msg)
    pubkey = PublicKey.from_signature_and_message(sig, msg, hasher=None)
    pubkey = pubkey.format(compressed=False)
    assert len(sig) == 65
    assert pubkey_to_addr(pubkey) == SENDER_ADDR


def test_balance_message_hash(client_contract_proxy: ChannelContractProxy):
    msg1 = balance_message_hash(RECEIVER_ADDR, 37, 15, CHANNEL_MANAGER_ADDRESS)
    assert len(msg1) == 32
    msg2 = client_contract_proxy.contract.call().balanceMessageHash(RECEIVER_ADDR, 37, 15)
    msg2 = force_bytes(msg2)
    assert msg1 == msg2


def test_sign_balance_proof(client_contract_proxy: ChannelContractProxy):
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 37, 15, CHANNEL_MANAGER_ADDRESS)
    sender_recovered = client_contract_proxy.contract.call().verifyBalanceProof(
        RECEIVER_ADDR, 37, 15, sig
    )
    assert sender_recovered == SENDER_ADDR


def test_verify_balance_proof():
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 31, 8, CHANNEL_MANAGER_ADDRESS)
    sender_recovered = verify_balance_proof(RECEIVER_ADDR, 31, 8, sig, CHANNEL_MANAGER_ADDRESS)
    assert sender_recovered == SENDER_ADDR


def test_closing_agreement_message_hash(client_contract_proxy: ChannelContractProxy):
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 13, 2, CHANNEL_MANAGER_ADDRESS)
    msg1 = closing_agreement_message_hash(sig)
    msg2 = client_contract_proxy.contract.call().closingAgreementMessageHash(sig)
    msg2 = force_bytes(msg2)
    assert msg1 == msg2


def test_sign_close(client_contract_proxy: ChannelContractProxy):
    balance_sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 13, 2, CHANNEL_MANAGER_ADDRESS
    )
    closing_sig = sign_close(RECEIVER_PRIVATE_KEY, balance_sig)

    receiver_recovered = client_contract_proxy.contract.call().verifyClosingSignature(
        balance_sig, closing_sig
    )
    assert receiver_recovered == RECEIVER_ADDR


def test_verify_closing_signature():
    balance_sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 101, 6, CHANNEL_MANAGER_ADDRESS
    )
    closing_sig = sign_close(RECEIVER_PRIVATE_KEY, balance_sig)

    receiver_recovered = verify_closing_signature(balance_sig, closing_sig)
    assert receiver_recovered == RECEIVER_ADDR

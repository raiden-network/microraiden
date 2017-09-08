import pytest  # noqa: F401
from coincurve import PublicKey
from eth_utils import encode_hex, decode_hex

from microraiden.contract_proxy import ChannelContractProxy
from microraiden.crypto import (
    privkey_to_addr,
    sha3_hex,
    sign,
    pubkey_to_addr,
    get_balance_message,
    sign_balance_proof,
    verify_balance_proof,
    eth_sign,
    sha3,
    addr_from_sig,
    eth_verify
)

SENDER_PRIVATE_KEY = '0xa0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0'
SENDER_ADDR = privkey_to_addr(SENDER_PRIVATE_KEY)
RECEIVER_PRIVATE_KEY = '0xb1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1'
RECEIVER_ADDR = privkey_to_addr(RECEIVER_PRIVATE_KEY)


def test_encode_hex():
    assert isinstance(encode_hex(b''), str)
    assert isinstance(decode_hex(''), bytes)


def test_sha3():
    addr1 = '0x1212121212121212121212121212121212121212'
    addr2 = '0x3434343434343434343434343434343434343434'

    assert sha3_hex('a') == '0x3ac225168df54212a25c1c01fd35bebfea408fdac2e31ddd6f80a4bbf9a5f1cb'
    assert sha3_hex('0x0a') == '0x0ef9d8f8804d174666011a394cab7901679a8944d24249fd148a6a36071151f8'
    assert (sha3_hex(addr1, (15, 32)) ==
            '0x1e17ec1733a759ef0d988fd0195d0e2792dc6181c8953130d14f9a261c6260bb')
    assert (sha3_hex(addr1, (17, 32), addr2) ==
            '0x00424f9e17d5fecf44d798962d27cd1d44ef37d3968b05a5ff078ff696c14ea8')
    assert (sha3_hex((23, 256)) ==
            '0xc624b66cc0138b8fabc209247f72d758e1cf3343756d543badbf24212bed8c15')
    assert sha3_hex(19) == '0x66de8ffda797e3de9c05e8fc57b3bf0ec28a930d40b0d285d93c06501cf6a090'
    assert sha3_hex(-5) == '0x7234c58e51ab4abdf62492ac6faf025ebff2afd4f861cebfa33d3e76667716a9'


def test_sign():
    msg = b'32' * 16
    assert len(msg) == 32
    sig = sign(SENDER_PRIVATE_KEY, msg)
    pubkey = PublicKey.from_signature_and_message(sig, msg, hasher=None)
    pubkey = pubkey.format(compressed=False)
    assert len(sig) == 65
    assert pubkey_to_addr(pubkey) == SENDER_ADDR


def test_eth_sign():
    # Generated using https://www.myetherwallet.com/signmsg.html
    msg = 'is it wednesday, my dudes?'

    sig_expected = '0xcc7b4e6cde6ace1d99995661250e52388aae17ebd66dcf52e634a6dd51bf286a2' \
                   'e9757967b7baff8b549da7d8c3340701abf8560430b7a0bdf34f42b19bbf1861b'

    assert encode_hex(eth_sign(SENDER_PRIVATE_KEY, msg)) == sig_expected


def test_get_balance_message():
    msg = get_balance_message(RECEIVER_ADDR, 310214, 14)
    assert msg == 'Receiver: {}, Balance: 14, Channel ID: 310214'.format(RECEIVER_ADDR)


def test_balance_message_contract(client_contract_proxy: ChannelContractProxy):
    msg1 = get_balance_message(RECEIVER_ADDR, 37, 15)
    msg2 = client_contract_proxy.contract.call().getBalanceMessage(RECEIVER_ADDR, 37, 15)
    assert msg1 == msg2


def test_sign_balance_proof_contract(client_contract_proxy: ChannelContractProxy):
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 37, 15)
    sender_recovered = client_contract_proxy.contract.call().verifyBalanceProof(
        RECEIVER_ADDR, 37, 15, sig
    )
    assert sender_recovered == SENDER_ADDR


def test_verify_balance_proof():
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 315123, 8)
    assert verify_balance_proof(RECEIVER_ADDR, 315123, 8, sig) == SENDER_ADDR


def test_sign_v0():
    msg = sha3('hello v=0')
    sig = sign(SENDER_PRIVATE_KEY, msg)
    assert sig[-1] == 1
    assert addr_from_sig(sig, msg) == SENDER_ADDR


def test_eth_sign_v27():
    sig = eth_sign(SENDER_PRIVATE_KEY, 'hello v=27')
    assert sig[-1] == 27
    assert eth_verify(sig, 'hello v=27') == SENDER_ADDR


def test_verify_balance_proof_v0():
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 312524, 11)
    sig = sig[:-1] + b'\x00'
    assert verify_balance_proof(RECEIVER_ADDR, 312524, 11, sig) == SENDER_ADDR


def test_verify_balance_proof_v27():
    # Should be default but test anyway.
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 312524, 11)
    sig = sig[:-1] + b'\x1b'
    assert verify_balance_proof(RECEIVER_ADDR, 312524, 11, sig) == SENDER_ADDR

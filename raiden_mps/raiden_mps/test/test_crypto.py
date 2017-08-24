import pytest
from coincurve import PublicKey
from eth_utils import force_bytes, encode_hex, decode_hex

from raiden_mps.test.config import CHANNEL_MANAGER_ADDRESS
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.crypto import (
    privkey_to_addr,
    sha3_hex,
    sign,
    pubkey_to_addr,
    balance_message,
    sign_balance_proof,
    verify_balance_proof,
    closing_agreement_message,
    sign_close,
    verify_closing_signature,
    eth_sign
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
    assert sha3_hex(addr1, (15, 32)) == \
           '0x1e17ec1733a759ef0d988fd0195d0e2792dc6181c8953130d14f9a261c6260bb'
    assert sha3_hex(addr1, (17, 32), addr2) == \
           '0x00424f9e17d5fecf44d798962d27cd1d44ef37d3968b05a5ff078ff696c14ea8'
    assert sha3_hex((23, 256)) == \
           '0xc624b66cc0138b8fabc209247f72d758e1cf3343756d543badbf24212bed8c15'
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


@pytest.mark.xfail
def test_balance_message_contract(
        client_contract_proxy: ChannelContractProxy,
        channel_manager_contract_address
):
    msg1 = balance_message(RECEIVER_ADDR, 37, 15, channel_manager_contract_address)
    assert len(msg1) == 32
    msg2 = client_contract_proxy.contract.call().balanceMessageHash(RECEIVER_ADDR, 37, 15)
    msg2 = force_bytes(msg2)
    assert msg1 == msg2


@pytest.mark.xfail
def test_sign_balance_proof_contract(
        client_contract_proxy: ChannelContractProxy,
        channel_manager_contract_address
):
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 37, 15, channel_manager_contract_address
    )
    sender_recovered = client_contract_proxy.contract.call().verifyBalanceProof(
        RECEIVER_ADDR, 37, 15, sig
    )
    assert sender_recovered == SENDER_ADDR


def test_verify_balance_proof(channel_manager_contract_address):
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 31, 8, channel_manager_contract_address
    )
    assert verify_balance_proof(
        SENDER_ADDR, RECEIVER_ADDR, 31, 8, sig, channel_manager_contract_address
    )


def test_verify_balance_proof_v0():
    sender = '0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38'
    receiver = '0x004b52c58863c903ab012537247b963c557929e8'
    contract_address = '0x5f3d7e2c44e157c2f1680059dd818d160e7d9625'
    sig = '0x3c18243343e3242222b05fddd9f629b7dbc04332ad551287623cbaf2592dabc46' \
          '6956ecfb3b859bbb17c0ad5990bac36f5edd92524a5160e9163a003f6d253a201'
    sig = decode_hex(sig)
    assert verify_balance_proof(sender, receiver, 3258574, 2, sig, contract_address)


@pytest.mark.xfail
def test_closing_agreement_message_contract(client_contract_proxy: ChannelContractProxy):
    sig = sign_balance_proof(SENDER_PRIVATE_KEY, RECEIVER_ADDR, 13, 2, CHANNEL_MANAGER_ADDRESS)
    msg1 = closing_agreement_message(sig)
    msg2 = client_contract_proxy.contract.call().closingAgreementMessageHash(sig)
    msg2 = force_bytes(msg2)
    assert msg1 == msg2


@pytest.mark.xfail
def test_sign_close_contract(client_contract_proxy: ChannelContractProxy):
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

    assert verify_closing_signature(RECEIVER_ADDR, balance_sig, closing_sig)

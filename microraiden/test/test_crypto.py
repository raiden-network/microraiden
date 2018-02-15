import pytest  # noqa: F401
from coincurve import PublicKey
from eth_utils import encode_hex, decode_hex, is_same_address
from web3.contract import Contract

from microraiden.utils import (
    privkey_to_addr,
    keccak256_hex,
    sign,
    pubkey_to_addr,
    sign_balance_proof,
    verify_balance_proof,
    eth_sign,
    keccak256,
    addr_from_sig,
    eth_verify,
    eth_sign_typed_data_message_eip,
    eth_sign_typed_data_eip,
    pack,
    sign_close,
    verify_closing_sig
)

SENDER_PRIVATE_KEY = '0xa0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0'
SENDER_ADDR = privkey_to_addr(SENDER_PRIVATE_KEY)
RECEIVER_PRIVATE_KEY = '0xb1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1'
RECEIVER_ADDR = privkey_to_addr(RECEIVER_PRIVATE_KEY)


def test_encode_hex():
    assert isinstance(encode_hex(b''), str)
    assert isinstance(decode_hex(''), bytes)


def test_pack():
    assert pack(False) == b'\x00'
    assert pack(True) == b'\x01'


def test_keccak256():
    addr1 = '0x1212121212121212121212121212121212121212'
    addr2 = '0x3434343434343434343434343434343434343434'

    ref = '0x3ac225168df54212a25c1c01fd35bebfea408fdac2e31ddd6f80a4bbf9a5f1cb'
    assert keccak256_hex('a') == ref

    ref = '0x0ef9d8f8804d174666011a394cab7901679a8944d24249fd148a6a36071151f8'
    assert keccak256_hex('0x0a') == ref

    ref = '0x1e17ec1733a759ef0d988fd0195d0e2792dc6181c8953130d14f9a261c6260bb'
    assert keccak256_hex(addr1, (15, 32)) == ref

    ref = '0x00424f9e17d5fecf44d798962d27cd1d44ef37d3968b05a5ff078ff696c14ea8'
    assert keccak256_hex(addr1, (17, 32), addr2) == ref

    ref = '0xc624b66cc0138b8fabc209247f72d758e1cf3343756d543badbf24212bed8c15'
    assert keccak256_hex((23, 256)) == ref

    ref = '0x66de8ffda797e3de9c05e8fc57b3bf0ec28a930d40b0d285d93c06501cf6a090'
    assert keccak256_hex(19) == ref

    ref = '0x7234c58e51ab4abdf62492ac6faf025ebff2afd4f861cebfa33d3e76667716a9'
    assert keccak256_hex(-5) == ref

    ref = '0x5fe7f977e71dba2ea1a68e21057beebb9be2ac30c6410aa38d4f3fbe41dcffd2'
    assert keccak256_hex(True) == ref

    ref = '0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a'
    assert keccak256_hex(False) == ref


def test_sign():
    msg = b'32' * 16
    assert len(msg) == 32
    sig = sign(SENDER_PRIVATE_KEY, msg)
    pubkey = PublicKey.from_signature_and_message(sig, msg, hasher=None)
    pubkey = pubkey.format(compressed=False)
    assert len(sig) == 65
    assert is_same_address(pubkey_to_addr(pubkey), SENDER_ADDR)


def test_eth_sign():
    # Generated using https://www.myetherwallet.com/signmsg.html
    msg = 'is it wednesday, my dudes?'

    sig_expected = '0xcc7b4e6cde6ace1d99995661250e52388aae17ebd66dcf52e634a6dd51bf286a2' \
                   'e9757967b7baff8b549da7d8c3340701abf8560430b7a0bdf34f42b19bbf1861b'

    assert encode_hex(eth_sign(SENDER_PRIVATE_KEY, msg)) == sig_expected


def test_eth_sign_typed_data():
    pass


def test_eth_sign_typed_data_eip():
    # Test cases from the EIP:
    # https://github.com/0xProject/EIPs/blob/01dfc0f9a4122d8ad8817c503447cab8efa8a6c4/EIPS/eip-signTypedData.md#test-cases
    privkey = 'f2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d'
    addr = '0x5409ed021d9299bf6814279a6a1411a7e866a631'
    assert is_same_address(addr, privkey_to_addr(privkey))

    typed_data = [('string', 'message', 'Hi, Alice!')]

    msg = eth_sign_typed_data_message_eip(typed_data)
    assert encode_hex(msg) == '0xe18794748cc6d73634d578f6a83f752bee11a0c9853d76bd0111d67a9b555a2c'

    sig = eth_sign_typed_data_eip(privkey, typed_data)
    sig_expected = '0x1a4ca93acf066a580f097690246e6c85d1deeb249194f6d3c2791f3aecb6adf8' \
                   '714ca4a0f12512ddd2a4f2393ea0c3b2c856279ba4929a5a34ae6859689428061b'
    assert encode_hex(sig) == sig_expected

    typed_data = [('uint', 'value', 42)]

    msg = eth_sign_typed_data_message_eip(typed_data)
    assert encode_hex(msg) == '0x6cb1c2645d841a0a3d142d1a2bdaa27015cc77f442e17037015b0350e468a957'

    sig = eth_sign_typed_data_eip(privkey, typed_data)
    sig_expected = '0x87c5b6a9f3a758babcc9140a96ae07957c6c9109af65bf139266cded52da49e6' \
                   '3df6af6f7daef588218e156bc83b95e0bfcfa8e72843cf4cf8c67c3ca11c3fd11b'
    assert encode_hex(sig) == sig_expected

    typed_data = [
        ('uint', 'value', 42),
        ('string', 'message', 'Hi, Alice!'),
        ('bool', 'removed', False)
    ]

    msg = eth_sign_typed_data_message_eip(typed_data)
    assert encode_hex(msg) == '0x36c3ed8591950e33dc4777bb455ab1a3e4223f84c42172a1ff2e200d5e25ee2e'

    sig = eth_sign_typed_data_eip(privkey, typed_data)
    sig_expected = '0x466a5a021225b681836e9951d2e603a37a605850ca26da0692ca532d4d1581d6' \
                   '031e2e3754fe31036e3a56d7e37fb6f598f7ab7a5cdd87aa04c9811c8b6209f31b'
    assert encode_hex(sig) == sig_expected


def test_sign_balance_proof_contract(channel_manager_contract: Contract):
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 37, 15, channel_manager_contract.address
    )
    sender_recovered = channel_manager_contract.call().extractBalanceProofSignature(
        RECEIVER_ADDR, 37, 15, sig
    )
    assert is_same_address(sender_recovered, SENDER_ADDR)


def test_verify_balance_proof(channel_manager_address: str):
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 315123, 8, channel_manager_address
    )
    assert is_same_address(verify_balance_proof(
        RECEIVER_ADDR, 315123, 8, sig, channel_manager_address
    ), SENDER_ADDR)


def test_sign_close_contract(channel_manager_contract: Contract):
    sig = sign_close(
        RECEIVER_PRIVATE_KEY, SENDER_ADDR, 315832, 13, channel_manager_contract.address
    )
    receiver_recovered = channel_manager_contract.call().extractClosingSignature(
        SENDER_ADDR, 315832, 13, sig
    )
    assert is_same_address(receiver_recovered, RECEIVER_ADDR)


def test_verify_closing_sign(channel_manager_address: str):
    sig = sign_close(
        RECEIVER_PRIVATE_KEY, SENDER_ADDR, 315832, 13, channel_manager_address
    )
    receiver_recovered = verify_closing_sig(SENDER_ADDR, 315832, 13, sig, channel_manager_address)
    assert is_same_address(receiver_recovered, RECEIVER_ADDR)


def test_sign_v0():
    msg = keccak256('hello v=0')
    sig = sign(SENDER_PRIVATE_KEY, msg)
    assert sig[-1] == 1
    assert is_same_address(addr_from_sig(sig, msg), SENDER_ADDR)


def test_eth_sign_v27():
    sig = eth_sign(SENDER_PRIVATE_KEY, 'hello v=27')
    assert sig[-1] == 27
    assert is_same_address(eth_verify(sig, 'hello v=27'), SENDER_ADDR)


def test_verify_balance_proof_v0(channel_manager_address: str):
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 312524, 11, channel_manager_address
    )
    sig = sig[:-1] + bytes([sig[-1] % 27])
    assert is_same_address(verify_balance_proof(
        RECEIVER_ADDR, 312524, 11, sig, channel_manager_address
    ), SENDER_ADDR)


def test_verify_balance_proof_v27(channel_manager_address: str):
    # Should be default but test anyway.
    sig = sign_balance_proof(
        SENDER_PRIVATE_KEY, RECEIVER_ADDR, 312524, 11, channel_manager_address
    )
    sig = sig[:-1] + bytes([sig[-1] % 27 + 27])
    assert is_same_address(verify_balance_proof(
        RECEIVER_ADDR, 312524, 11, sig, channel_manager_address
    ), SENDER_ADDR)

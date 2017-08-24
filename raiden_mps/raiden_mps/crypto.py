"""
Convention within this module is to only add the '0x' hex prefix to addresses while other
hex-encoded values, such as hashes and private keys, come without a 0x prefix.
"""

from coincurve import PrivateKey, PublicKey
from eth_utils import encode_hex, decode_hex, remove_0x_prefix, keccak, is_0x_prefixed, \
    is_same_address


def generate_privkey() -> bytes:
    return encode_hex(PrivateKey().secret)


def pubkey_to_addr(pubkey) -> str:
    if isinstance(pubkey, PublicKey):
        pubkey = pubkey.format(compressed=False)
    assert isinstance(pubkey, bytes)
    return encode_hex(sha3(pubkey[1:])[-20:])


def privkey_to_addr(privkey: str) -> str:
    return pubkey_to_addr(PrivateKey.from_hex(remove_0x_prefix(privkey)).public_key)


def addr_from_sig(sig: bytes, msg: bytes):
    assert len(sig) == 65
    # Support Ethereum's EC v value of 27.
    if sig[-1] >= 27:
        sig = sig[:-1] + bytes([sig[-1] - 27])

    receiver_pubkey = PublicKey.from_signature_and_message(sig, msg, hasher=None)
    return pubkey_to_addr(receiver_pubkey)


def addr_from_eth_sig(sig: bytes, msg: bytes):
    return addr_from_sig(sig, eth_message_hash(encode_hex(msg)))


def pack(*args) -> bytes:
    """
    Simulates Solidity's sha3 packing. Integers can be passed as tuples where the second tuple
    element specifies the variable's size in bits, e.g.:
    sha3((5, 32))
    would be equivalent to Solidity's
    sha3(uint32(5))
    Default size is 256.
    """
    def format_int(value, size):
        assert isinstance(value, int)
        assert isinstance(size, int)
        if value >= 0:
            return decode_hex('{:x}'.format(value).zfill(size // 4))
        else:
            return decode_hex('{:x}'.format((1 << size) + value))

    msg = b''
    for arg in args:
        assert arg
        if isinstance(arg, bytes):
            msg += arg
        elif isinstance(arg, str):
            if is_0x_prefixed(arg):
                msg += decode_hex(arg)
            else:
                msg += arg.encode()
        elif isinstance(arg, int):
            msg += format_int(arg, 256)
        elif isinstance(arg, tuple):
            msg += format_int(arg[0], arg[1])
        else:
            raise ValueError('Unsupported type: {}.'.format(type(arg)))

    return msg


def sha3(*args) -> bytes:
    return keccak(pack(*args))


def sha3_hex(*args) -> bytes:
    return encode_hex(sha3(*args))


def sign(privkey: str, msg: bytes) -> bytes:
    assert isinstance(msg, bytes)
    assert isinstance(privkey, str)

    pk = PrivateKey.from_hex(remove_0x_prefix(privkey))
    assert len(msg) == 32

    sig = pk.sign_recoverable(msg, hasher=None)
    assert len(sig) == 65

    return sig


def eth_message_hash(msg: str) -> bytes:
    msg = '\x19Ethereum Signed Message:\n' + str(len(msg)) + msg
    return sha3(msg)


def eth_sign(privkey: str, msg: str) -> bytes:
    assert isinstance(msg, str)
    sig = sign(privkey, eth_message_hash(msg))
    sig = sig[:-1] + bytes([sig[-1] + 27])
    return sig


def verify_sig(expected_signer: str, sig: bytes, msg: bytes) -> bool:
    # TODO: waiting for the day to drop support for the deprecated way
    # Try the 'standard' way using prefixed `eth_sign` on the encoded string, then old raw sign.
    return is_same_address(addr_from_eth_sig(sig, msg), expected_signer) or \
        is_same_address(addr_from_sig(sig, sha3(msg)), expected_signer.lower())


def balance_message(
        receiver: str, open_block_number: int, balance: int, contract_address: str
) -> bytes:
    return pack(receiver, (open_block_number, 32), (balance, 192), contract_address)


def sign_balance_proof(
        privkey: str, receiver: str, open_block_number: int, balance: int, contract_address: str
) -> bytes:
    msg = balance_message(receiver, open_block_number, balance, contract_address)
    return eth_sign(privkey, encode_hex(msg))


def verify_balance_proof(
        sender: str,
        receiver: str,
        open_block_number: int,
        balance: int,
        balance_sig: bytes,
        contract_address: str
) -> bool:
    msg = balance_message(receiver, open_block_number, balance, contract_address)
    return verify_sig(sender, balance_sig, msg)


def closing_agreement_message(balance_sig: bytes) -> bytes:
    return pack(balance_sig)


def sign_close(privkey: str, balance_sig: bytes) -> bytes:
    msg = closing_agreement_message(balance_sig)
    closing_sig = eth_sign(privkey, encode_hex(msg))

    return closing_sig


def verify_closing_signature(receiver:str , balance_sig: bytes, closing_sig: bytes) -> bool:
    msg = closing_agreement_message(balance_sig)
    return verify_sig(receiver, closing_sig, msg)

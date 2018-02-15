from typing import List, Tuple, Any

from coincurve import PrivateKey, PublicKey
from eth_utils import (
    encode_hex,
    decode_hex,
    remove_0x_prefix,
    keccak,
    is_0x_prefixed,
    to_checksum_address
)
from ethereum.transactions import Transaction
import rlp


Type = str
Name = str
TypedData = Tuple[Type, Name, Any]


def generate_privkey() -> bytes:
    return encode_hex(PrivateKey().secret)


def pubkey_to_addr(pubkey) -> str:
    if isinstance(pubkey, PublicKey):
        pubkey = pubkey.format(compressed=False)
    assert isinstance(pubkey, bytes)
    return encode_hex(keccak256(pubkey[1:])[-20:])


def privkey_to_addr(privkey: str) -> str:
    return to_checksum_address(
        pubkey_to_addr(PrivateKey.from_hex(remove_0x_prefix(privkey)).public_key)
    )


def addr_from_sig(sig: bytes, msg: bytes):
    assert len(sig) == 65
    # Support Ethereum's EC v value of 27 and EIP 155 values of > 35.
    if sig[-1] >= 35:
        network_id = (sig[-1] - 35) // 2
        sig = sig[:-1] + bytes([sig[-1] - 35 - 2 * network_id])
    elif sig[-1] >= 27:
        sig = sig[:-1] + bytes([sig[-1] - 27])

    receiver_pubkey = PublicKey.from_signature_and_message(sig, msg, hasher=None)
    return pubkey_to_addr(receiver_pubkey)


def pack(*args) -> bytes:
    """
    Simulates Solidity's keccak256 packing. Integers can be passed as tuples where the second tuple
    element specifies the variable's size in bits, e.g.:
    keccak256((5, 32))
    would be equivalent to Solidity's
    keccak256(uint32(5))
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
        assert arg is not None
        if isinstance(arg, bytes):
            msg += arg
        elif isinstance(arg, str):
            if is_0x_prefixed(arg):
                msg += decode_hex(arg)
            else:
                msg += arg.encode()
        elif isinstance(arg, bool):
            msg += format_int(int(arg), 8)
        elif isinstance(arg, int):
            msg += format_int(arg, 256)
        elif isinstance(arg, tuple):
            msg += format_int(arg[0], arg[1])
        else:
            raise ValueError('Unsupported type: {}.'.format(type(arg)))

    return msg


def keccak256(*args) -> bytes:
    return keccak(pack(*args))


def keccak256_hex(*args) -> bytes:
    return encode_hex(keccak256(*args))


def sign(privkey: str, msg: bytes, v=0) -> bytes:
    assert isinstance(msg, bytes)
    assert isinstance(privkey, str)

    pk = PrivateKey.from_hex(remove_0x_prefix(privkey))
    assert len(msg) == 32

    sig = pk.sign_recoverable(msg, hasher=None)
    assert len(sig) == 65

    sig = sig[:-1] + bytes([sig[-1] + v])

    return sig


def sign_transaction(tx: Transaction, privkey: str, network_id: int):
    # Implementing EIP 155.
    tx.v = network_id
    sig = sign(privkey, keccak256(rlp.encode(tx)), v=35 + 2 * network_id)
    v, r, s = sig[-1], sig[0:32], sig[32:-1]
    tx.v = v
    tx.r = int.from_bytes(r, byteorder='big')
    tx.s = int.from_bytes(s, byteorder='big')


def eth_message_hash(msg: str) -> bytes:
    msg = '\x19Ethereum Signed Message:\n' + str(len(msg)) + msg
    return keccak256(msg)


def eth_sign(privkey: str, msg: str) -> bytes:
    assert isinstance(msg, str)
    sig = sign(privkey, eth_message_hash(msg), v=27)
    return sig


def eth_verify(sig: bytes, msg: str) -> str:
    return addr_from_sig(sig, eth_message_hash(msg))


def eth_sign_typed_data_message(typed_data: List[TypedData]) -> bytes:
    typed_data = [('{} {}'.format(type_, name), data) for type_, name, data in typed_data]
    schema, data = [list(zipped) for zipped in zip(*typed_data)]

    return keccak256(keccak256(*schema), keccak256(*data))


def eth_sign_typed_data(privkey: str, typed_data: List[TypedData]) -> bytes:
    msg = eth_sign_typed_data_message(typed_data)
    return sign(privkey, msg, v=27)


def eth_sign_typed_data_message_eip(typed_data: List[TypedData]) -> bytes:
    typed_data = [('{} {}'.format(type_, name), data) for type_, name, data in typed_data]
    schema, data = [list(zipped) for zipped in zip(*typed_data)]

    return keccak256(keccak256(*schema), *data)


def eth_sign_typed_data_eip(privkey: str, typed_data: List[TypedData]) -> bytes:
    msg = eth_sign_typed_data_message_eip(typed_data)
    return sign(privkey, msg, v=27)


def get_balance_message(
        receiver: str, open_block_number: int, balance: int, contract_address: str
) -> bytes:
    return eth_sign_typed_data_message([
        ('string', 'message_id', 'Sender balance proof signature'),
        ('address', 'receiver', receiver),
        ('uint32', 'block_created', (open_block_number, 32)),
        ('uint192', 'balance', (balance, 192)),
        ('address', 'contract', contract_address)
    ])


def sign_balance_proof(
        privkey: str, receiver: str, open_block_number: int, balance: int, contract_address: str
) -> bytes:
    msg = get_balance_message(receiver, open_block_number, balance, contract_address)
    return sign(privkey, msg, v=27)


def verify_balance_proof(
        receiver: str,
        open_block_number: int,
        balance: int,
        balance_sig: bytes,
        contract_address: str
) -> str:
    msg = get_balance_message(receiver, open_block_number, balance, contract_address)
    return addr_from_sig(balance_sig, msg)


def get_closing_message(
        sender: str,
        open_block_number: int,
        balance: int,
        contract_address: str
) -> bytes:
    return eth_sign_typed_data_message([
        ('string', 'message_id', 'Receiver closing signature'),
        ('address', 'sender', sender),
        ('uint32', 'block_created', (open_block_number, 32)),
        ('uint192', 'balance', (balance, 192)),
        ('address', 'contract', contract_address)
    ])


def sign_close(
        privkey: str,
        sender: str,
        open_block_number: int,
        balance: int,
        contract_address: str
) -> bytes:
    msg = get_closing_message(sender, open_block_number, balance, contract_address)
    return sign(privkey, msg, v=27)


def verify_closing_sig(
        sender: str,
        open_block_number: int,
        balance: int,
        closing_sig: bytes,
        contract_address: str
) -> str:
    msg = get_closing_message(sender, open_block_number, balance, contract_address)
    return addr_from_sig(closing_sig, msg)

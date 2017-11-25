import binascii
import bitcoin
from ethereum import utils
from secp256k1 import PrivateKey
from eth_utils import encode_hex
from utils.utils import sol_sha3


eth_prefix = "\x19Ethereum Signed Message:\n"


def eth_privtoaddr(priv) -> str:
    pub = bitcoin.encode_pubkey(bitcoin.privtopub(priv), 'bin_electrum')
    return "0x" + binascii.hexlify(sol_sha3(pub)[12:]).decode("ascii")


def eth_message_prefixed(msg: str) -> bytes:
    return eth_prefix + str(len(msg)) + msg


def eth_message_hex(msg: str) -> bytes:
    msg = eth_message_prefixed(msg)
    msg_hex = encode_hex(msg)
    return sol_sha3(msg_hex)


def eth_signed_typed_data_message(types, names, data) -> bytes:
    """
    types e.g. ('address', 'uint', ('uint', 32))
    names e.g. ('receiver', 'block_created', 'balance')
    data e.g. ('0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb', 3000, 1000)
    """
    assert len(types) == len(data) == len(names), 'Argument length mismatch.'

    sign_types = []
    sign_values = []
    for i, type in enumerate(types):
        if isinstance(type, tuple):
            sign_types.append(type[0] + str(type[1]))
            sign_values.append((data[i], type[1]))
        else:
            sign_types.append(type)
            sign_values.append(data[i])

        sign_types[i] += ' ' + names[i]

    return sol_sha3(sol_sha3(*sign_types), sol_sha3(*sign_values))


def sign(data: bytes, private_key_seed_ascii: str):
    priv = private_key_seed_ascii
    pk = PrivateKey(priv, raw=True)
    signature = pk.ecdsa_recoverable_serialize(pk.ecdsa_sign_recoverable(data, raw=True))
    signature = signature[0] + utils.bytearray_to_bytestr([signature[1]])
    return signature, eth_privtoaddr(priv)


def check(data: bytes, pk: bytes):
    return sign(data, pk)

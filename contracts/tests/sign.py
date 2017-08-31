import binascii
import bitcoin
from ethereum import utils
from ethereum.utils import sha3
from secp256k1 import PrivateKey
from eth_utils import keccak, is_0x_prefixed, decode_hex, encode_hex


eth_prefix = "\x19Ethereum Signed Message:\n"

def eth_privtoaddr(priv) -> str:
    pub = bitcoin.encode_pubkey(bitcoin.privtopub(priv), 'bin_electrum')
    return "0x" + binascii.hexlify(sha3(pub)[12:]).decode("ascii")


def eth_message_hex(msg: str) -> bytes:
    msg = eth_prefix + str(len(msg)) + msg
    print("--eth_message_hex msg", msg)
    msg_hex = encode_hex(msg)
    print("---eth_message_hex hex", msg_hex)
    return sha3(msg_hex)


def sign(data: str, private_key_seed_ascii: str):
    data = eth_message_hex(data)
    print("--eth_message_hex hash", data)
    priv = private_key_seed_ascii
    pk = PrivateKey(priv, raw=True)
    signature = pk.ecdsa_recoverable_serialize(pk.ecdsa_sign_recoverable(data, raw=True))
    signature = signature[0] + utils.bytearray_to_bytestr([signature[1]])
    return signature, eth_privtoaddr(priv)


def check(data: bytes, pk: bytes):
    return sign(data, pk)


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

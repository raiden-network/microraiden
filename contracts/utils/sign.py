import binascii
import bitcoin
from ethereum import utils
from secp256k1 import PrivateKey
from eth_utils import encode_hex
from utils.utils import sha3


eth_prefix = "\x19Ethereum Signed Message:\n"


def eth_privtoaddr(priv) -> str:
    pub = bitcoin.encode_pubkey(bitcoin.privtopub(priv), 'bin_electrum')
    return "0x" + binascii.hexlify(sha3(pub)[12:]).decode("ascii")


def eth_message_hex(msg: str) -> bytes:
    msg = eth_prefix + str(len(msg)) + msg
    msg_hex = encode_hex(msg)
    return sha3(msg_hex)


def sign(data: str, private_key_seed_ascii: str):
    data = eth_message_hex(data)
    priv = private_key_seed_ascii
    pk = PrivateKey(priv, raw=True)
    signature = pk.ecdsa_recoverable_serialize(pk.ecdsa_sign_recoverable(data, raw=True))
    signature = signature[0] + utils.bytearray_to_bytestr([signature[1]])
    return signature, eth_privtoaddr(priv)


def check(data: bytes, pk: bytes):
    return sign(data, pk)

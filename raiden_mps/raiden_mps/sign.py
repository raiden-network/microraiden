from coincurve import PrivateKey

def sign(privkey, msg):
    pk = PrivateKey.from_hex(privkey)
    assert len(msg) == 32

    sig = pk.sign_recoverable(msg, hasher=None)
    assert len(sig) == 65

    sig = sig[:-1] + chr(sig[-1]).encode()

    return sig

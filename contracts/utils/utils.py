from eth_utils import keccak, is_0x_prefixed, decode_hex, encode_hex


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

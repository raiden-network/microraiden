import getpass
import json
import logging

import os
import stat

from eth_utils import is_hex, decode_hex, encode_hex
from ethereum import keys

log = logging.getLogger(__name__)


def check_permission_safety(path):
    """Check if the file at the given path is safe to use as a state file.

    This checks that group and others have no permissions on the file and that the current user is
    the owner.
    """
    f_stats = os.stat(path)
    return (f_stats.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0 and f_stats.st_uid == os.getuid()


def get_private_key(key_path, password_path=None):
    """Open a JSON-encoded private key and return it

    If a password file is provided, uses it to decrypt the key. If not, the
    password is asked interactively. Raw hex-encoded private keys are supported,
    but deprecated."""

    assert key_path, key_path
    if not os.path.exists(key_path):
        log.fatal("%s: no such file", key_path)
        return None

    if not check_permission_safety(key_path):
        log.fatal("Private key file %s must be readable only by its owner.", key_path)
        return None

    if password_path and not check_permission_safety(password_path):
        log.fatal("Password file %s must be readable only by its owner.", password_path)
        return None

    with open(key_path) as keyfile:
        private_key = keyfile.readline().strip()

        if is_hex(private_key) and len(decode_hex(private_key)) == 32:
            log.warning("Private key in raw format. Consider switching to JSON-encoded")
        else:
            keyfile.seek(0)
            try:
                json_data = json.load(keyfile)
                if password_path:
                    with open(password_path) as password_file:
                        password = password_file.readline().strip()
                else:
                    password = getpass.getpass("Enter the private key password: ")
                private_key = encode_hex(keys.decode_keystore_json(json_data, password))
            except ValueError:
                log.fatal("Invalid private key format or password!")
                return None

    return private_key

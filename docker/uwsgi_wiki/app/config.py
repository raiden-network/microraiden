import os
from microraiden import config
from microraiden.crypto import privkey_to_addr
from microraiden.utils import get_private_key

# private key of the content provider
PRIVATE_KEY_FILE = '/tmp/key.json'
PASSWORD_FILE = '/tmp/password.txt'
PRIVATE_KEY = get_private_key(PRIVATE_KEY_FILE, PASSWORD_FILE)
RECEIVER_ADDRESS = privkey_to_addr(PRIVATE_KEY)

# host and port Parity/Geth serves RPC requests on
WEB3_PROVIDER = 'http://web3:8545'
# state file to store proxy state and balance proofs
STATE_FILE = "/files/%s_%s.db" % (config.CHANNEL_MANAGER_ADDRESS[:10], RECEIVER_ADDRESS[:10])
SLEEP_RELOAD = 2

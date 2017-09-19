from microraiden import config
from microraiden.crypto import privkey_to_addr

# private key of the content provider
PRIVATE_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
RECEIVER_ADDRESS = privkey_to_addr(PRIVATE_KEY)
# host and port Parity/Geth serves RPC requests on
RPC_PROVIDER = 'http://172.17.0.1:8180'
# state file to store proxy state and balance proofs
STATE_FILE = "/files/%s_%s.json" % (config.CHANNEL_MANAGER_ADDRESS[:10], RECEIVER_ADDRESS[:10])
SLEEP_RELOAD = 2

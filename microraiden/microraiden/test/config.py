import os
from eth_utils import denoms
from microraiden.utils import privkey_to_addr

CHANNEL_MANAGER_ADDRESS = '0xeb244b0502a2d3867e5cab2347c6e1cdeb5e1eef'
API_PATH = "/api/1"

MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

FAUCET_PRIVKEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
FAUCET_ADDRESS = privkey_to_addr(FAUCET_PRIVKEY)
FAUCET_ALLOWANCE = 10**23
INITIAL_TOKEN_SUPPLY = 10**25
SENDER_ETH_ALLOWANCE = int(0.02 * denoms.ether)
SENDER_TOKEN_ALLOWANCE = 10**20
RECEIVER_ETH_ALLOWANCE = int(0.02 * denoms.ether)
RECEIVER_TOKEN_ALLOWANCE = 0

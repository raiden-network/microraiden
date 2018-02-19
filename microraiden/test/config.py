import os
from eth_utils import denoms

API_PATH = "/api/1"

MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

FAUCET_ALLOWANCE = 10 * denoms.ether
INITIAL_TOKEN_SUPPLY = 10**25
SENDER_ETH_ALLOWANCE = int(0.5 * denoms.ether)
SENDER_TOKEN_ALLOWANCE = 10**14
RECEIVER_ETH_ALLOWANCE = int(0.5 * denoms.ether)
RECEIVER_TOKEN_ALLOWANCE = 0

import os
from eth_utils import denoms
from microraiden.crypto import privkey_to_addr

CHANNEL_MANAGER_ADDRESS = '0xeb244b0502a2d3867e5cab2347c6e1cdeb5e1eef'
TOKEN_ADDRESS = '0xc97c510f7d79057c8ae98e0ff8b3841e824cb4b5'
API_PATH = "/api/1"
GAS_LIMIT = 200000
GAS_PRICE = 5 * denoms.gwei

MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

FAUCET_PRIVKEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
FAUCET_ADDRESS = privkey_to_addr(FAUCET_PRIVKEY)
SENDER_ETH_ALLOWANCE = int(0.02 * denoms.ether)
SENDER_TOKEN_ALLOWANCE = 100
RECEIVER_ETH_ALLOWANCE = int(0.02 * denoms.ether)
RECEIVER_TOKEN_ALLOWANCE = 0

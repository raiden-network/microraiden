import json
import os
from eth_utils import denoms
from collections import namedtuple

API_PATH = "/api/1"
GAS_LIMIT = 130000

# Plain old transaction, for lack of a better term.
POT_GAS_LIMIT = 21000
GAS_PRICE = 20 * denoms.gwei

NETWORK_NAMES = {
    1: 'mainnet',
    2: 'morden',
    3: 'ropsten',
    4: 'rinkeby',
    30: 'rootstock-main',
    31: 'rootstock-test',
    42: 'kovan',
    61: 'etc-main',
    62: 'etc-test',
    1337: 'geth'
}

NetworkConfig = namedtuple('NetworkConfig', 'channel_manager_address start_block')

# address of the default channel manager contract. You can change this using commandline
# option --channel-manager-address when running the proxy
NETWORK_CONFIG = {
    '1': NetworkConfig('0x0', 0),
    '3': NetworkConfig('0x161a0d7726EB8B86EB587d8BD483be1CE87b0609', 2400640),
    '42': NetworkConfig('0xB9721dF0e024114e7B25F2cF503d8CBE3D52b400', 5230017)
}
# map NETWORK_CONFIG to a network_id: manager_address dict
CHANNEL_MANAGER_ADDRESS = {
    k: v.channel_manager_address for k, v in NETWORK_CONFIG.items()
}
# map NETWORK_CONFIG to a network_id: sync_block dict
START_SYNC_BLOCK = {
    k: v.start_block for k, v in NETWORK_CONFIG.items()
}
# absolute path to this directory. Used to find path to the webUI sources
MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# webUI sources
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
# javascript library for microraiden
JSLIB_DIR = os.path.join(HTML_DIR, 'js')
# url prefix for jslib dir
JSPREFIX_URL = '/js'
# decimals of the token. Any price that's set for the proxy resources is multiplied by this.
TKN_DECIMALS = 10**18  # token decimals

# ethereum node RPC interface should be available here
WEB3_PROVIDER_DEFAULT = "http://127.0.0.1:8545"

# name of the channel manager contract
CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'
# name of the token contract
TOKEN_ABI_NAME = 'CustomToken'
# compiled contracts path
CONTRACTS_ABI_JSON = 'data/contracts.json'

with open(os.path.join(MICRORAIDEN_DIR, 'microraiden', CONTRACTS_ABI_JSON)) as metadata_file:
    CONTRACT_METADATA = json.load(metadata_file)

# required version of the deployed contract at CHANNEL_MANAGER_ADDRESS.
# Proxy will refuse to start if the versions do not match.
MICRORAIDEN_VERSION = "0.1.0"
CHANNEL_MANAGER_CONTRACT_VERSION = MICRORAIDEN_VERSION
# they should stay the same until we decide otherwise
assert MICRORAIDEN_VERSION == CHANNEL_MANAGER_CONTRACT_VERSION
#  proxy will stop serving requests if receiver balance is below PROXY_BALANCE_LIMIT
PROXY_BALANCE_LIMIT = 10**8
SLEEP_RELOAD = 2


# sanity checks
assert PROXY_BALANCE_LIMIT > 0
assert isinstance(PROXY_BALANCE_LIMIT, int)

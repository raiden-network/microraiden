"""
This file contains configuration constants you probably don't need to change
"""
import json
import os


def read_version(path: str):
    return open(path, 'r').read().strip()


# api path prefix
API_PATH = "/api/1"
"""str: api path prefix"""
MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
"""str: absolute path to module directory. Used to find path to the webUI sources"""
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
"""str: webUI sources directory"""
JSLIB_DIR = os.path.join(HTML_DIR, 'js')
"""str: javascript directory"""
JSPREFIX_URL = '/js'
"""str: url prefix for jslib dir"""
TKN_DECIMALS = 10**18
"""int: decimals of the token.
Any price that's set for the proxy resources is multiplied by this."""

WEB3_PROVIDER_DEFAULT = "http://127.0.0.1:8545"
"""str: ethereum node RPC interface URL"""

CHANNEL_MANAGER_ABI_NAME = 'RaidenMicroTransferChannels'
"""str: name of the channel manager contract"""
TOKEN_ABI_NAME = 'CustomToken'
"""str: name of the token contract"""
CONTRACTS_ABI_JSON = 'data/contracts.json'
"""str: compiled contracts path"""

with open(os.path.join(MICRORAIDEN_DIR, 'microraiden', CONTRACTS_ABI_JSON)) as metadata_file:
    CONTRACT_METADATA = json.load(metadata_file)

MICRORAIDEN_VERSION = read_version(os.path.join(MICRORAIDEN_DIR, 'microraiden', 'VERSION'))
"""str: version of Microraiden library"""
CHANNEL_MANAGER_CONTRACT_VERSION = "0.2.0"
"""str: required version of the deployed contract at CHANNEL_MANAGER_ADDRESS.
Proxy will refuse to start if the major or minor versions do not match."""
PROXY_BALANCE_LIMIT = 10**8
"""int: proxy will stop serving requests if receiver balance is below PROXY_BALANCE_LIMIT"""
SLEEP_RELOAD = 2

# sanity checks
assert PROXY_BALANCE_LIMIT > 0
assert isinstance(PROXY_BALANCE_LIMIT, int)

# map network id to network name
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
    1337: 'geth',

    65536: 'ethereum-tester'
}


def get_network_id(network_name: str):
    """
    Map canonical network name to its integer id.

    Args:
        network_name (str): network name

    Returns:
        int: network id
    """
    ids = list(NETWORK_NAMES.keys())
    return ids[list(NETWORK_NAMES.values()).index(network_name)]

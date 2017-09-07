import os
from web3 import HTTPProvider

CHANNEL_MANAGER_ADDRESS = '0xeb244b0502a2d3867e5cab2347c6e1cdeb5e1eef'
TOKEN_ADDRESS = '0xc97c510f7d79057c8ae98e0ff8b3841e824cb4b5'
API_PATH = "/api/1"
GAS_LIMIT = 250000
GAS_PRICE = 20 * 1000 * 1000 * 1000

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

MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

WEB3_PROVIDER = HTTPProvider("http://127.0.0.1:8545", request_kwargs={'timeout': 60})

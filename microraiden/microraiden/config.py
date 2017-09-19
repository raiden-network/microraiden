import os
from eth_utils import denoms
from web3 import HTTPProvider

API_PATH = "/api/1"
GAS_LIMIT = 250000
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

CHANNEL_MANAGER_ADDRESS = '0x00ef252b7cefa53b729f064d40ba9373643f73cc'
TOKEN_ADDRESS = '0xadd159c1ed9b0619f31aff09ef34f508a0d44108'
MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

WEB3_PROVIDER = HTTPProvider("http://127.0.0.1:8545", request_kwargs={'timeout': 60})

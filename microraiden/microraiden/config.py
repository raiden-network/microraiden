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

CHANNEL_MANAGER_ADDRESS = '0xffa52825c7997dd2be80fb91080500a52abd6d5b'
TOKEN_ADDRESS = '0x04c7f744a0c751d89e99ae79a39060ec6f3c4397'
MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

WEB3_PROVIDER = HTTPProvider("http://127.0.0.1:8545", request_kwargs={'timeout': 60})

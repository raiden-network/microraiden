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

CHANNEL_MANAGER_ADDRESS = '0xa9b370c05016cf99a2f4760e837b932a4cc648f5'
TOKEN_ADDRESS = '0xefa17deefde69542c8def9cd6f3840ad51a986ce'
MICRORAIDEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(MICRORAIDEN_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

WEB3_PROVIDER = HTTPProvider("http://127.0.0.1:8545", request_kwargs={'timeout': 60})

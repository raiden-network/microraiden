import os

CHANNEL_MANAGER_ADDRESS = '0x7e1528bfc6c3fd9863055bb0d4f89d69aaacdb5c'
TOKEN_ADDRESS = '0x6b3da80008814e116a3963065b77928be91cfa93'
API_PATH = "/api/1"
GAS_LIMIT = 150000
GAS_PRICE = 20 * 1000 * 1000 * 1000

RAIDEN_MPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(RAIDEN_MPS_DIR, 'raiden_mps', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

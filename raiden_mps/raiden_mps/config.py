import os

CHANNEL_MANAGER_ADDRESS = '0x770ba2be480504ccc703672e7053e857ba4c8f67'
TOKEN_ADDRESS = '0xe2aece17096c95b97329e90205eab8673d1d72b7'
API_PATH = "/api/1"
GAS_LIMIT = 250000
GAS_PRICE = 20 * 1000 * 1000 * 1000

RAIDEN_MPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_DIR = os.path.join(RAIDEN_MPS_DIR, 'raiden_mps', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

import os
from eth_utils import denoms
from microraiden.crypto import privkey_to_addr

CHANNEL_MANAGER_ADDRESS = '0xeb244b0502a2d3867e5cab2347c6e1cdeb5e1eef'
TOKEN_ADDRESS = '0xc97c510f7d79057c8ae98e0ff8b3841e824cb4b5'
API_PATH = "/api/1"
GAS_LIMIT = 200000
GAS_PRICE = 20 * denoms.gwei

RAIDEN_MPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HTML_DIR = os.path.join(RAIDEN_MPS_DIR, 'microraiden', 'webui')
JSLIB_DIR = os.path.join(HTML_DIR, 'js')

# Testing keys and addresses.

#   0x0052d7b657553e7f47239d8c4431fef001a7f99c
TEST_SENDER_PRIVKEY = '558ce5d09417f127c89097f8c41def07883cbec094da79f5dddfd4590607f7c2'
#   0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38
# TEST_SENDER_PRIVKEY = '028f5efe7cb1d42997603a05d85d744031d5d5b5d187b132a7d42bb8c0de2ad4'
#   0x004b52c58863c903ab012537247b963c557929e8
TEST_RECEIVER_PRIVKEY = 'b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
#   0xd1bf222ef7289ae043b723939d86c8a91f3aac3f
TEST_SECONDARY_RECEIVER_PRIVKEY = '883f724ea3fa17728f759d3999f92aa46fee224f24efc09e4a354ba3f7b29411'

TEST_SENDER_ADDR = privkey_to_addr(TEST_SENDER_PRIVKEY)
TEST_RECEIVER_ADDR = privkey_to_addr(TEST_RECEIVER_PRIVKEY)

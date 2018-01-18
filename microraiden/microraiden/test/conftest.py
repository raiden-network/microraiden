from microraiden.test.fixtures import * # flake8: noqa
from gevent import monkey
monkey.patch_all(thread=False) # thread is false due to clash when testing both contract/microraiden modules
import logging
import os
import microraiden.config as config

config.START_SYNC_BLOCK = 0

# to disable annoying 'test.rpc eth_getBlockNumber' message
logging.getLogger('testrpc.rpc').setLevel(logging.WARNING)

# test if both $DISPLAY and tkinter library are available
try:
    import tkinter
    os.environ['DISPLAY']
except (ImportError, KeyError):
    os.environ['TEST_SKIP_XORG'] = '1'

def pytest_addoption(parser):
    parser.addoption(
        "--no-tester",
        action="store_false",
        default=True,
        dest='use_tester',
        help="use a real RPC endpoint instead of the tester chain"
    )
    parser.addoption(
        "--no-clean-channels",
        action="store_false",
        default=True,
        dest='clean_channels',
        help="prevent all channels from closing cooperatively before and after each test"
    )
    parser.addoption(
        "--faucet-private-key",
        default='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        dest='faucet_private_key',
        help="the private key to an address with sufficient ETH and RDN tokens to run tests on a "
             "real network, specified either as a file path or a hex-encoded private key"
    )
    parser.addoption(
        "--faucet-password-path",
        default='',
        dest='faucet_password_path',
        help="the path to a file containing the password to the faucet's encrypted private key"
    )
    parser.addoption(
        "--private-key-seed",
        default=14789632,
        dest='private_key_seed',
        help="the seed for private key generation for addresses used in tests"
    )

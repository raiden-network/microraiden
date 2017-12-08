from microraiden.test.fixtures import * # flake8: noqa
from gevent import monkey
monkey.patch_all(thread=False) # thread is false due to clash when testing both contract/microraiden modules
import logging

# to disable annoying 'test.rpc eth_getBlockNumber' message
logging.getLogger('testrpc.rpc').setLevel(logging.WARNING)


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

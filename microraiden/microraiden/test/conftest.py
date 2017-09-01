from microraiden.test.fixtures import * # flake8: noqa
from gevent import monkey
monkey.patch_all(thread=False) # thread is false due to clash when testing both contract/microraiden modules


def pytest_addoption(parser):
    parser.addoption("--no-tester", action="store_false", default=True, dest='use_tester',
                     help="connect to RPC node for testing")

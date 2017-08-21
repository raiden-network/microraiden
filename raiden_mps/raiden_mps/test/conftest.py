from gevent import monkey
monkey.patch_all()
from raiden_mps.test.fixtures import *


def pytest_addoption(parser):
    parser.addoption("--no-tester", action="store_false", default=True, dest='use_tester',
                     help="connect to RPC node for testing")

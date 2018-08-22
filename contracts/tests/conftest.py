#
# disable thread patching - contract tests that use web3 didn't
#  work properly
#
from gevent import monkey
monkey.patch_all(thread=False)

from .fixtures import *  # noqa
from .fixtures_uraiden import *  # noqa

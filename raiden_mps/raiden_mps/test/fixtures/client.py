import pytest
import tempfile
import shutil

from raiden_mps.client.rmp_client import RMPClient

from ethereum.utils import privtoaddr, encode_hex


@pytest.fixture
def client_privkey():
    return '558ce5d09417f127c89097f8c41def07883cbec094da79f5dddfd4590607f7c2'


@pytest.fixture
def client_address(client_privkey):
    return '0x' + encode_hex(privtoaddr(client_privkey))


@pytest.fixture
def rpc_endpoint():
    return 'localhost'


@pytest.fixture
def rpc_port():
    return 8545


@pytest.fixture
def datadir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def rmp_client(client_privkey, rpc_endpoint, rpc_port, datadir):
    return RMPClient(
        client_privkey,
        rpc_endpoint,
        rpc_port,
        datadir
    )

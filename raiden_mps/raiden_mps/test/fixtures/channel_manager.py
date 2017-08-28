import logging
import pytest
import gevent
import types
from populus.wait import Wait
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.channel_manager import ChannelManager, Blockchain
from web3 import Web3, EthereumTesterProvider
from web3.providers.rpc import RPCProvider
from raiden_mps.test.config import (
    CHANNEL_MANAGER_ADDRESS,
    TOKEN_ADDRESS,
    GAS_PRICE,
    GAS_LIMIT
)


@pytest.fixture
def mine_sync_event():
    return gevent.event.Event()


@pytest.fixture(scope='session', autouse=True)
def disable_requests_loggin():
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


@pytest.fixture
def use_tester(request):
    return request.config.getoption('use_tester')

@pytest.fixture
def channel_managers_count():
    return 2


def deploy_token_contract(web3, deployer_address, token_abi, token_bytecode, sender_address):
    Token = web3.eth.contract(abi=token_abi, bytecode=token_bytecode)
    txhash = Token.deploy({'from': deployer_address}, args=[100000, "RDNToken", 6, "RDN"])
    receipt = web3.eth.getTransactionReceipt(txhash)
    contract_address = receipt.contractAddress
    token = Token(contract_address)
    for friend in [sender_address]:
        token.transact({'from': deployer_address}).transfer(friend, 10000)
    assert web3.eth.getCode(contract_address) != '0x'
    return token


def deploy_channel_manager_contract(web3, deployer_address, channel_manager_abi,
                                    channel_manager_bytecode, token_contract_address):
    ChannelManager = web3.eth.contract(abi=channel_manager_abi, bytecode=channel_manager_bytecode)
    txhash = ChannelManager.deploy({'from': deployer_address}, args=[token_contract_address, 30])
    contract_address = web3.eth.getTransactionReceipt(txhash).contractAddress
    web3.testing.mine(1)
    return ChannelManager(contract_address)


@pytest.fixture
def token_contract_address(use_tester, web3, deployer_address, token_abi, token_bytecode,
                           sender_address):
    if use_tester:
        contract = deploy_token_contract(web3, deployer_address, token_abi, token_bytecode,
                                         sender_address)
        return contract.address
    else:
        return TOKEN_ADDRESS


@pytest.fixture
def channel_manager_contract_address(use_tester, web3, deployer_address, channel_manager_abi,
                                     channel_manager_bytecode, token_contract_address):
    if use_tester:
        contract = deploy_channel_manager_contract(web3, deployer_address, channel_manager_abi,
                                                   channel_manager_bytecode,
                                                   token_contract_address)
        return contract.address
    else:
        return CHANNEL_MANAGER_ADDRESS


@pytest.fixture
def web3(use_tester, deployer_address, mine_sync_event):
    if use_tester:
        provider = EthereumTesterProvider()
        web3 = Web3(provider)
        x = web3.testing.mine

        def mine_patched(self, count):
            x(count)
            mine_sync_event.set()
            gevent.sleep(0)
            mine_sync_event.clear()

        web3.testing.mine = types.MethodType(
            mine_patched, web3.testing.mine)
    else:
        rpc = RPCProvider('localhost', 8545)
        return Web3(rpc)
    return web3


@pytest.fixture
def wait(web3, kovan_block_time):
    poll_interval = kovan_block_time / 2
    return Wait(web3, poll_interval=poll_interval)


@pytest.fixture
def wait_for_blocks(web3, kovan_block_time, use_tester):
    def wait_for_blocks(n):
        if use_tester:
            web3.testing.mine(n)
            gevent.sleep(0)
        else:
            target_block = web3.eth.blockNumber + n
            while web3.eth.blockNumber < target_block:
                gevent.sleep(kovan_block_time / 2)
    return wait_for_blocks


@pytest.fixture
def channel_manager_contract_proxies(web3, receiver_privkeys, channel_manager_contract_address,
                                     channel_manager_abi, use_tester):
    return [ChannelContractProxy(web3, key, channel_manager_contract_address,
                                 channel_manager_abi, GAS_PRICE, GAS_LIMIT,
                                 tester_mode=use_tester)
            for key in receiver_privkeys]


@pytest.fixture
def token_contract(web3, token_contract_address, token_abi):
    return web3.eth.contract(abi=token_abi, address=token_contract_address)


def start_channel_manager(channel_manager, use_tester, mine_sync_event):
    # disable logging during sync
#    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    if use_tester:
        x = channel_manager.blockchain._update

        def update_patched(self: Blockchain):
            x()
            mine_sync_event.wait()

        channel_manager.blockchain._update = types.MethodType(
            update_patched, channel_manager.blockchain)
        channel_manager.blockchain.poll_frequency = 0

    def fail(greenlet):
        raise greenlet.exception

    channel_manager.link_exception(fail)
    channel_manager.start()
#    channel_manager.wait_sync()
#    logging.getLogger('channel_manager').setLevel(logging.DEBUG)
    return channel_manager


@pytest.fixture
def channel_managers(web3, channel_manager_contract_proxies, receiver_privkeys,
                     token_contract, use_tester, mine_sync_event):
#    logging.getLogger('channel_manager').setLevel(logging.WARNING)
    channel_managers = [ChannelManager(web3, proxy, token_contract, privkey)
                        for privkey, proxy in
                        zip(receiver_privkeys, channel_manager_contract_proxies)]
    for manager in channel_managers:
        start_channel_manager(manager, use_tester, mine_sync_event)
    return channel_managers


@pytest.fixture
def channel_manager(channel_managers):
    return channel_managers[0]

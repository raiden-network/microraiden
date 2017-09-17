import logging
import pytest
import gevent
import types

import rlp
from eth_utils import decode_hex
from ethereum.transactions import Transaction
import ethereum.tester
from populus.wait import Wait

from microraiden.contract_proxy import (
    ChannelContractProxy,
    ContractProxy,
)
from web3 import Web3, EthereumTesterProvider
from web3.providers.rpc import RPCProvider

from microraiden.crypto import (
    addr_from_sig,
    sha3,
)
from microraiden.test.config import (
    CHANNEL_MANAGER_ADDRESS,
    TOKEN_ADDRESS,
    FAUCET_ADDRESS,
    FAUCET_PRIVKEY,
    GAS_PRICE,
    GAS_LIMIT,
)


@pytest.fixture(scope='session')
def mine_sync_event():
    return gevent.event.Event()


@pytest.fixture(scope='session', autouse=True)
def disable_requests_loggin():
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def deploy_token_contract(web3, deployer_address, token_abi, token_bytecode):
    Token = web3.eth.contract(abi=token_abi, bytecode=token_bytecode)
    txhash = Token.deploy({'from': deployer_address}, args=[100000, "ERC223", 6, "ERC223"])
    receipt = web3.eth.getTransactionReceipt(txhash)
    contract_address = receipt.contractAddress
    token = Token(contract_address)
    token.transact({'from': deployer_address}).transfer(FAUCET_ADDRESS, 10000)
    assert web3.eth.getCode(contract_address) != '0x'
    return token


def deploy_channel_manager_contract(web3, deployer_address, channel_manager_abi,
                                    channel_manager_bytecode, token_contract_address):
    ChannelManager = web3.eth.contract(abi=channel_manager_abi, bytecode=channel_manager_bytecode)
    txhash = ChannelManager.deploy({'from': deployer_address}, args=[token_contract_address, 30])
    contract_address = web3.eth.getTransactionReceipt(txhash).contractAddress
    web3.testing.mine(1)
    return ChannelManager(contract_address)


@pytest.fixture(scope='session')
def token_contract_address(use_tester, web3, deployer_address, token_abi, token_bytecode):
    if use_tester:
        contract = deploy_token_contract(web3, deployer_address, token_abi, token_bytecode)
        return contract.address
    else:
        return TOKEN_ADDRESS


@pytest.fixture(scope='session')
def channel_manager_contract_address(use_tester, web3, deployer_address, channel_manager_abi,
                                     channel_manager_bytecode, token_contract_address):
    if use_tester:
        contract = deploy_channel_manager_contract(web3, deployer_address, channel_manager_abi,
                                                   channel_manager_bytecode,
                                                   token_contract_address)
        return contract.address
    else:
        return CHANNEL_MANAGER_ADDRESS


@pytest.fixture(scope='session')
def web3(request, use_tester, deployer_address, mine_sync_event):
    if use_tester:
        provider = EthereumTesterProvider()
        web3 = Web3(provider)
        x = web3.testing.mine

        def mine_patched(self, count):
            x(count)
            mine_sync_event.set()
            gevent.sleep(0)  # switch context
            mine_sync_event.clear()

        web3.testing.mine = types.MethodType(
            mine_patched, web3.testing.mine
        )

        # Tester chain uses Transaction to send and validate transactions but does not support
        # EIP-155 yet. This patches the sender address recovery to handle EIP-155.
        sender_property_original = Transaction.sender.fget

        def sender_property_patched(self: Transaction):
            if self._sender:
                return self._sender

            if self.v and self.v >= 35:
                v = bytes([self.v])
                r = self.r.to_bytes(32, byteorder='big')
                s = self.s.to_bytes(32, byteorder='big')
                raw_tx = Transaction(
                    self.nonce, self.gasprice, self.startgas, self.to, self.value, self.data,
                    (self.v - 35) // 2, 0, 0
                )
                msg = sha3(rlp.encode(raw_tx))
                self._sender = decode_hex(addr_from_sig(r + s + v, msg))
                return self._sender
            else:
                return sender_property_original(self)

        Transaction.sender = property(
            sender_property_patched,
            Transaction.sender.fset,
            Transaction.sender.fdel
        )

        # add faucet account to tester
        ethereum.tester.accounts.append(decode_hex(FAUCET_ADDRESS))
        ethereum.tester.keys.append(decode_hex(FAUCET_PRIVKEY))

        def remove_faucet_account():
            ethereum.tester.accounts.remove(decode_hex(FAUCET_ADDRESS))
            ethereum.tester.keys.remove(decode_hex(FAUCET_PRIVKEY))
        request.addfinalizer(remove_faucet_account)

        # make faucet rich
        web3.eth.sendTransaction({'to': FAUCET_ADDRESS, 'value': 10**23})

    else:
        rpc = RPCProvider('localhost', 8545)
        return Web3(rpc)
    return web3


@pytest.fixture(scope='session')
def wait(web3, kovan_block_time):
    poll_interval = kovan_block_time / 2
    return Wait(web3, poll_interval=poll_interval)


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='session')
def wait_for_transaction(wait):
    def wait_for_transaction(tx_hash):
        wait.for_receipt(tx_hash)
        gevent.sleep(0)
    return wait_for_transaction


@pytest.fixture(scope='session')
def make_channel_manager_proxy(web3, channel_manager_contract_address, channel_manager_abi,
                               use_tester):
    def channel_manager_proxy_factory(privkey):
        return ChannelContractProxy(
            web3,
            privkey,
            channel_manager_contract_address,
            channel_manager_abi,
            GAS_PRICE, GAS_LIMIT,
            use_tester
        )
    return channel_manager_proxy_factory


@pytest.fixture(scope='session')
def make_token_proxy(web3, token_contract_address, token_abi, use_tester):
    def token_proxy_factory(privkey):
        return ContractProxy(
            web3,
            privkey,
            token_contract_address,
            token_abi,
            GAS_PRICE, GAS_LIMIT,
            use_tester
        )
    return token_proxy_factory


@pytest.fixture
def token_contract(web3, token_contract_address, token_abi):
    return web3.eth.contract(abi=token_abi, address=token_contract_address)

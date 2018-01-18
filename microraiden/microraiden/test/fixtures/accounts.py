import logging
from typing import List

import pytest

from eth_utils import (
    decode_hex,
    encode_hex,
    is_hex,
    remove_0x_prefix,
    keccak
)
import ethereum.tester
from web3 import Web3
from web3.contract import Contract

from microraiden.utils import (
    privkey_to_addr,
    create_signed_contract_transaction,
    create_signed_transaction,
    get_private_key
)
from microraiden.config import NETWORK_CFG
from microraiden.test.config import (
    RECEIVER_ETH_ALLOWANCE,
    RECEIVER_TOKEN_ALLOWANCE,
    SENDER_ETH_ALLOWANCE,
    SENDER_TOKEN_ALLOWANCE
)


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def private_key_seed(request) -> int:
    return request.config.getoption('private_key_seed')


@pytest.fixture(scope='session')
def private_keys(private_key_seed: int) -> List[str]:
    """
    Note: using 0 as the seed computes tester coinbase as the first address. This might cause
    issues, especially on sweeping all of these accounts, as the coinbase cannot be swept.
    """
    return [encode_hex(keccak(str(private_key_seed + i))) for i in range(10)]


@pytest.fixture(scope='session')
def faucet_password_path(request) -> str:
    return request.config.getoption('faucet_password_path')


@pytest.fixture(scope='session')
def faucet_private_key(request, faucet_password_path: str) -> str:
    private_key = request.config.getoption('faucet_private_key')
    if is_hex(private_key):
        assert len(remove_0x_prefix(private_key)) == 64
        return private_key
    else:
        private_key = get_private_key(private_key, faucet_password_path)
        assert private_key is not None, 'Error loading faucet private key from file.'
        return private_key


@pytest.fixture(scope='session')
def faucet_address(faucet_private_key: str):
    return privkey_to_addr(faucet_private_key)


@pytest.fixture(scope='session')
def make_account(
        request,
        web3: Web3,
        wait_for_transaction,
        use_tester: bool,
        token_contract: Contract,
        faucet_private_key: str,
        faucet_address: str
):
    def account_factory(eth_allowance: int, token_allowance: int, private_key: str):
        address = privkey_to_addr(private_key)
        if use_tester:
            ethereum.tester.accounts.append(decode_hex(address))
            ethereum.tester.keys.append(decode_hex(private_key))
        fund_account(
            address,
            eth_allowance,
            token_allowance,
            token_contract,
            web3,
            wait_for_transaction,
            faucet_private_key
        )

        def finalize():
            sweep_account(private_key, faucet_address, token_contract, web3, wait_for_transaction)
            if use_tester:
                ethereum.tester.accounts.remove(decode_hex(address))
                ethereum.tester.keys.remove(decode_hex(private_key))
        request.addfinalizer(finalize)
        return private_key
    return account_factory


def fund_account(
        address: str,
        eth_allowance: int,
        token_allowance: int,
        token_contract: Contract,
        web3: Web3,
        wait_for_transaction,
        faucet_private_key: str,
):
    log.info('Funding account {}'.format(address))
    tx = create_signed_transaction(
        faucet_private_key,
        web3,
        to=address,
        value=eth_allowance
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)

    if token_allowance > 0:
        tx = create_signed_contract_transaction(
            faucet_private_key,
            token_contract,
            'transfer',
            [
                address,
                token_allowance
            ]
        )
        tx_hash = web3.eth.sendRawTransaction(tx)
        wait_for_transaction(tx_hash)


def sweep_account(
        private_key: str,
        faucet_address: str,
        token_contract: Contract,
        web3: Web3,
        wait_for_transaction
):
    address = privkey_to_addr(private_key)
    log.info('Sweeping account {}'.format(address))
    token_balance = token_contract.call().balanceOf(address)
    if token_balance > 0:
        tx = create_signed_contract_transaction(
            private_key,
            token_contract,
            'transfer',
            [
                faucet_address,
                token_balance
            ]
        )
        try:
            tx_hash = web3.eth.sendRawTransaction(tx)
        except ValueError as e:
            if e.args[0]['message'].startswith('Insufficient funds.'):
                pass
            else:
                raise
        else:
            wait_for_transaction(tx_hash)
            assert token_contract.call().balanceOf(address) == 0

    balance = web3.eth.getBalance(address)
    if balance < NETWORK_CFG.POT_GAS_LIMIT * NETWORK_CFG.GAS_PRICE:
        return
    tx = create_signed_transaction(
        private_key,
        web3,
        to=faucet_address,
        value=balance - NETWORK_CFG.POT_GAS_LIMIT * NETWORK_CFG.GAS_PRICE,
        gas_limit=NETWORK_CFG.POT_GAS_LIMIT
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)
    assert web3.eth.getBalance(address) == 0, (
        'Sweeping of account {} (private key {}) failed.'.format(address, private_key)
    )


@pytest.fixture(scope='session')
def sender_privkey(make_account, private_keys: List[str]):
    return make_account(SENDER_ETH_ALLOWANCE, SENDER_TOKEN_ALLOWANCE, private_keys[0])


@pytest.fixture(scope='session')
def sender_address(sender_privkey):
    return privkey_to_addr(sender_privkey)


@pytest.fixture(scope='session')
def receiver_privkey(make_account, private_keys: List[str]):
    return make_account(RECEIVER_ETH_ALLOWANCE, RECEIVER_TOKEN_ALLOWANCE, private_keys[1])


@pytest.fixture(scope='session')
def receiver_address(receiver_privkey):
    return privkey_to_addr(receiver_privkey)

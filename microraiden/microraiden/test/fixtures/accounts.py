import pytest
import random

from eth_utils import (
    decode_hex,
    encode_hex,
    int_to_big_endian,
    pad_left,
)
import ethereum.tester
from web3 import Web3
from web3.contract import Contract

from microraiden.utils import (
    privkey_to_addr,
    create_signed_contract_transaction,
    create_signed_transaction
)
from microraiden.config import GAS_PRICE
from microraiden.test.config import (
    RECEIVER_ETH_ALLOWANCE,
    RECEIVER_TOKEN_ALLOWANCE,
    SENDER_ETH_ALLOWANCE,
    SENDER_TOKEN_ALLOWANCE,
    FAUCET_PRIVKEY,
    FAUCET_ADDRESS,
)


def random_private_key(bound):
    """Randomly gnerate a private key smaller than a certain bound."""
    n = random.randint(1, bound)  # nosec
    private_key = encode_hex(pad_left(int_to_big_endian(n), 32, '\0'))
    return private_key


@pytest.fixture(scope='session')
def make_account(
        request,
        web3: Web3,
        wait_for_transaction,
        use_tester: bool,
        token_contract: Contract
):
    def account_factory(eth_allowance, token_allowance):
        privkey = random_private_key(1000)
        address = privkey_to_addr(privkey)
        if use_tester:
            ethereum.tester.accounts.append(decode_hex(address))
            ethereum.tester.keys.append(decode_hex(privkey))
        fund_account(
            address,
            eth_allowance,
            token_allowance,
            token_contract,
            web3,
            wait_for_transaction
        )

        def finalize():
            sweep_account(privkey, token_contract, web3, wait_for_transaction)
            if use_tester:
                ethereum.tester.accounts.remove(decode_hex(address))
                ethereum.tester.keys.remove(decode_hex(privkey))
        request.addfinalizer(finalize)
        return privkey
    return account_factory


def fund_account(
        address: str,
        eth_allowance: int,
        token_allowance: int,
        token_contract: Contract,
        web3: Web3,
        wait_for_transaction
):
    tx = create_signed_transaction(
        FAUCET_PRIVKEY,
        web3,
        to=address,
        value=eth_allowance,
        gas_limit=21000
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)

    if token_allowance > 0:
        tx = create_signed_contract_transaction(
            FAUCET_PRIVKEY,
            token_contract,
            'transfer',
            [
                address,
                token_allowance
            ]
        )
        tx_hash = web3.eth.sendRawTransaction(tx)
        wait_for_transaction(tx_hash)


def sweep_account(private_key: str, token_contract: Contract, web3: Web3, wait_for_transaction):
    address = privkey_to_addr(private_key)
    token_balance = token_contract.call().balanceOf(address)
    if token_balance > 0:
        tx = create_signed_contract_transaction(
            private_key,
            token_contract,
            'transfer',
            [
                FAUCET_ADDRESS,
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

    balance = web3.eth.getBalance(address, 'pending')
    if balance < 21000 * GAS_PRICE:
        return
    tx = create_signed_transaction(
        private_key,
        web3,
        to=FAUCET_ADDRESS,
        value=balance - 21000 * GAS_PRICE,
        gas_limit=21000
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    wait_for_transaction(tx_hash)
    assert web3.eth.getBalance(address, 'pending') == 0, (
        'Sweeping of account {} (private key {}) failed.'.format(address, private_key)
    )


@pytest.fixture
def sender_privkey(make_account):
    return make_account(SENDER_ETH_ALLOWANCE, SENDER_TOKEN_ALLOWANCE)


@pytest.fixture
def sender_address(sender_privkey):
    return privkey_to_addr(sender_privkey)


@pytest.fixture
def receiver_privkey(make_account):
    return make_account(RECEIVER_ETH_ALLOWANCE, RECEIVER_TOKEN_ALLOWANCE)


@pytest.fixture
def receiver_address(receiver_privkey):
    return privkey_to_addr(receiver_privkey)

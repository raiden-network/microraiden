import pytest
import random

from eth_utils import (
    decode_hex,
    encode_hex,
    int_to_big_endian,
    pad_left,
)
from ethereum.transactions import Transaction
import ethereum.tester
import rlp

from microraiden.crypto import (
    privkey_to_addr,
    sign_transaction
)
from microraiden.test.config import (
    GAS_PRICE,
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
def make_account(request, make_token_proxy, web3, wait_for_transaction, use_tester):
    def account_factory(eth_allowance, token_allowance):
        privkey = random_private_key(1000)
        address = privkey_to_addr(privkey)
        if use_tester:
            ethereum.tester.accounts.append(decode_hex(address))
            ethereum.tester.keys.append(decode_hex(privkey))
        fund_account(privkey, eth_allowance, token_allowance, make_token_proxy, web3,
                     wait_for_transaction)

        def finalize():
            sweep_account(privkey, make_token_proxy, web3, wait_for_transaction)
            if use_tester:
                ethereum.tester.accounts.remove(decode_hex(address))
                ethereum.tester.keys.remove(decode_hex(privkey))
        request.addfinalizer(finalize)
        return privkey
    return account_factory


def fund_account(privkey, eth_allowance, token_allowance, make_token_proxy, web3,
                 wait_for_transaction):
    address = privkey_to_addr(privkey)
    tx = Transaction(
        nonce=web3.eth.getTransactionCount(FAUCET_ADDRESS, 'pending'),
        gasprice=GAS_PRICE,
        startgas=21000,
        to=decode_hex(address),
        value=eth_allowance,
        data=b'',
        v=0, r=0, s=0
    )
    sign_transaction(tx, FAUCET_PRIVKEY, web3.version.network)
    tx_hash = web3.eth.sendRawTransaction(encode_hex(rlp.encode(tx)))
    wait_for_transaction(tx_hash)

    if token_allowance > 0:
        faucet_token_proxy = make_token_proxy(FAUCET_PRIVKEY)
        tx = faucet_token_proxy.create_signed_transaction('transfer',
                                                          [decode_hex(address), token_allowance])
        tx_hash = web3.eth.sendRawTransaction(tx)
        wait_for_transaction(tx_hash)


def sweep_account(privkey, make_token_proxy, web3, wait_for_transaction):
    address = privkey_to_addr(privkey)
    token_proxy = make_token_proxy(privkey)
    token_balance = token_proxy.contract.call().balanceOf(address)
    if token_balance > 0:
        tx = token_proxy.create_signed_transaction('transfer',
                                                   [decode_hex(FAUCET_ADDRESS), token_balance])
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
    tx = Transaction(
        nonce=web3.eth.getTransactionCount(address, 'pending'),
        gasprice=GAS_PRICE,
        startgas=21000,
        to=FAUCET_ADDRESS,
        value=balance - 21000 * GAS_PRICE,
        data=b'',
        v=0, r=0, s=0
    )
    sign_transaction(tx, privkey, web3.version.network)
    tx_hash = web3.eth.sendRawTransaction(encode_hex(rlp.encode(tx)))
    wait_for_transaction(tx_hash)
    assert web3.eth.getBalance(address, 'pending') == 0, ('sweeping of account {} '
                                                          '(private key {}) failed')


@pytest.fixture
def sender_privkey(make_account, make_token_proxy):
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

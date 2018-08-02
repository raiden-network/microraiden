import pytest
from utils.logs import LogHandler
from tests.constants import PASSPHRASE


# recheck test_create_token_fallback_uint_conversion when bug bounty limit is removed
contract_args = [
    {
        'decimals': 18,
        'supply': 10 ** 26,
        'challenge_period': 500
    },
    {
        'decimals': 0,
        'supply': 10 ** 26,
        'challenge_period': 502
    }
]
channel_values = [
    {
        'deposit': 450,
        'balance': 0,
        'type': '20'
    },
    {
        'deposit': 100 * 10 ** 18,
        'balance': 55 * 10 ** 18,
        'type': '223'
    },
    {
        'deposit': 100 * 10 ** 18,
        'balance': 100 * 10 ** 18,
        'type': '223'
    }
]


@pytest.fixture()
def enable_logs():
    return False


@pytest.fixture(params=contract_args)
def contract_params(request):
    return request.param


@pytest.fixture(params=channel_values)
def channel_params(request):
    return request.param


@pytest.fixture()
def owner_index():
    return 1


@pytest.fixture()
def owner(web3, owner_index):
    return web3.eth.accounts[owner_index]


@pytest.fixture()
def get_accounts(web3, owner_index, create_accounts):
    def get(number, index_start=None):
        if not index_start:
            index_start = owner_index + 1
        accounts_len = len(web3.eth.accounts)
        index_end = min(number + index_start, accounts_len)
        accounts = web3.eth.accounts[index_start:index_end]
        if number > len(accounts):
            accounts += create_accounts(number - len(accounts))
        return accounts
    return get


@pytest.fixture()
def create_accounts(web3):
    def get(number):
        new_accounts = []
        for i in range(0, number):
            new_account = web3.personal.newAccount(PASSPHRASE)
            amount = int(web3.eth.getBalance(web3.eth.accounts[0]) / 2 / number)
            web3.eth.sendTransaction({
                'from': web3.eth.accounts[0],
                'to': new_account,
                'value': amount
            })
            web3.personal.unlockAccount(new_account, PASSPHRASE)
            new_accounts.append(new_account)
        return new_accounts
    return get


@pytest.fixture
def create_contract(chain, owner):
    def get(contract_type, arguments, transaction=None):
        if not transaction:
            transaction = {}
        if 'from' not in transaction:
            transaction['from'] = owner

        deploy_txn_hash = contract_type.deploy(transaction=transaction, args=arguments)
        contract_address = chain.wait.for_contract_address(deploy_txn_hash)
        contract = contract_type(address=contract_address)
        return contract
    return get


@pytest.fixture()
def event_handler(chain, web3):
    def get(contract=None, address=None, abi=None):
        if contract:
            # Get contract factory name from contract instance
            # TODO is there an actual API for this??
            comp_target = contract.metadata['settings']['compilationTarget']
            name = comp_target[list(comp_target.keys())[0]]

            abi = chain.provider.get_base_contract_factory(name).abi
            address = contract.address

        if address and abi:
            return LogHandler(web3, address, abi)
        else:
            raise Exception('event_handler called without a contract instance')
    return get


@pytest.fixture()
def get_token_contract(chain, create_contract):
    def get(arguments, transaction=None):
        CustomToken = chain.provider.get_contract_factory('CustomToken')
        token_contract = create_contract(CustomToken, arguments, transaction)
        return token_contract
    return get


@pytest.fixture
def txn_cost(web3, txnGas):
    def get(txn_hash):
        return txnGas(txn_hash) * web3.eth.gasPrice
    return get


@pytest.fixture
def txn_gas(chain):
    def get(txn_hash):
        receipt = chain.wait.for_receipt(txn_hash)
        return receipt['gasUsed']
    return get


@pytest.fixture
def print_gas(chain, txn_gas):
    def get(txn_hash, message=None, additional_gas=0):
        gas_used = txn_gas(txn_hash)
        if not message:
            message = txn_hash

        print('----------------------------------')
        print('GAS USED ' + message, gas_used + additional_gas)
        print('----------------------------------')
    return get


@pytest.fixture()
def get_block(chain):
    def get(txn_hash):
        receipt = chain.wait.for_receipt(txn_hash)
        return receipt['blockNumber']
    return get

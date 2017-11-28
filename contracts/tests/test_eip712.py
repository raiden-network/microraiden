import pytest
from ethereum import tester
from utils import sign
from tests.utils import balance_proof_hash
from tests.fixtures import (
    owner_index,
    owner,
    contract_params,
    create_contract,
    get_token_contract,
    get_accounts,
    create_accounts,
    empty_address
)
from tests.fixtures_uraiden import (
    token_contract,
    token_instance,
    get_uraiden_contract,
    uraiden_contract,
    uraiden_instance,
    eip712_contract,
    eip712_instance
)


def test_eip712_instance_fixture(uraiden_instance):
    assert uraiden_instance.call().microraiden_eip712_helper()


def test_eip712_instance(owner, get_accounts, uraiden_contract, eip712_contract, eip712_instance):
    uraiden_instance = uraiden_contract()
    (A, B) = get_accounts(2)
    assert uraiden_instance.call().microraiden_eip712_helper() == empty_address
    uraiden_instance.transact({'from': owner}).setEip712HelperContract(eip712_instance.address)
    assert uraiden_instance.call().microraiden_eip712_helper() == eip712_instance.address

    # Test eip712_instance address change
    eip712_instance2 = eip712_contract()
    assert eip712_instance.address != eip712_instance2.address

    # Only owner can change this
    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).setEip712HelperContract(eip712_instance2.address)

    uraiden_instance.transact({'from': owner}).setEip712HelperContract(eip712_instance2.address)
    assert uraiden_instance.call().microraiden_eip712_helper() == eip712_instance2.address


def test_getMessageHash(get_accounts, uraiden_instance, eip712_instance):
    (A, B) = get_accounts(2)
    receiver = '0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb'
    block = 4804175
    balance = 22000000000000000000

    message_hash = sign.eth_signed_typed_data_message(
        ('address', ('uint', 32), ('uint', 192), 'address'),
        ('receiver', 'block_created', 'balance', 'contract'),
        (receiver, block, balance, uraiden_instance.address)
    )

    eip712_message_hash = eip712_instance.call().getMessageHash(
        receiver,
        block,
        balance,
        uraiden_instance.address
    )
    # TODO
    # assert eip712_message_hash == message_hash

    eip712_message_hash = eip712_instance.call().getMessageHash(
        A,
        block,
        balance,
        uraiden_instance.address
    )

    eip712_message_hash = eip712_instance.call().getMessageHash(
        receiver,
        10,
        balance,
        uraiden_instance.address
    )
    assert eip712_message_hash != message_hash

    eip712_message_hash = eip712_instance.call().getMessageHash(
        receiver,
        block,
        20,
        uraiden_instance.address
    )
    assert eip712_message_hash != message_hash

    eip712_message_hash = eip712_instance.call().getMessageHash(
        receiver,
        block,
        balance,
        A
    )
    assert eip712_message_hash != message_hash

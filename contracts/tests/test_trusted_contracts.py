import pytest
from ethereum import tester
from tests.constants import (
    CHALLENGE_PERIOD_MIN,
    FAKE_ADDRESS,
    EMPTY_ADDRESS,
    URAIDEN_EVENTS,
)
from tests.utils import (
    checkTrustedEvent,
)


def test_trusted_contracts_constructor(
        owner,
        get_accounts,
        get_uraiden_contract,
        uraiden_contract,
        token_instance,
        delegate_contract,
        contract_params,
):
    trusted_contract = delegate_contract()
    trusted_contract2 = delegate_contract()
    other_contract = delegate_contract()
    simple_account = get_accounts(1)[0]
    uraiden = uraiden_contract(token_instance, [trusted_contract.address])

    assert uraiden.call().trusted_contracts(trusted_contract.address)
    assert not uraiden.call().trusted_contracts(other_contract.address)

    with pytest.raises(TypeError):
        get_uraiden_contract([token_instance.address, CHALLENGE_PERIOD_MIN])
    with pytest.raises(TypeError):
        get_uraiden_contract([token_instance.address, CHALLENGE_PERIOD_MIN, [FAKE_ADDRESS]])

    uraiden2 = get_uraiden_contract([
        token_instance.address,
        CHALLENGE_PERIOD_MIN,
        [trusted_contract2.address, EMPTY_ADDRESS, simple_account]
    ])
    assert uraiden2.call().trusted_contracts(trusted_contract2.address)
    assert not uraiden2.call().trusted_contracts(EMPTY_ADDRESS)
    assert not uraiden2.call().trusted_contracts(simple_account)


def test_add_trusted_contracts_call(owner, get_accounts, uraiden_instance, delegate_contract):
    (A, B) = get_accounts(2)

    with pytest.raises(TypeError):
        uraiden_instance.transact({'from': owner}).addTrustedContracts([FAKE_ADDRESS])

    uraiden_instance.transact({'from': owner}).addTrustedContracts([])
    uraiden_instance.transact({'from': owner}).addTrustedContracts([EMPTY_ADDRESS])


def test_add_trusted_contracts_only_owner(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract
):
    (A, B) = get_accounts(2)
    trusted_contract = delegate_contract()

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).addTrustedContracts([trusted_contract.address])

    uraiden_instance.transact({'from': owner}).addTrustedContracts([trusted_contract.address])
    assert uraiden_instance.call().trusted_contracts(trusted_contract.address)


def test_add_trusted_contracts_state(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract,
        print_gas
):
    (A, B) = get_accounts(2)
    trusted_contract1 = delegate_contract()
    trusted_contract2 = delegate_contract()
    trusted_contract3 = delegate_contract()
    trusted_contract4 = delegate_contract()

    assert not uraiden_instance.call().trusted_contracts(trusted_contract1.address)
    assert not uraiden_instance.call().trusted_contracts(trusted_contract2.address)
    assert not uraiden_instance.call().trusted_contracts(trusted_contract3.address)
    assert not uraiden_instance.call().trusted_contracts(trusted_contract4.address)

    uraiden_instance.transact({'from': owner}).addTrustedContracts([A])
    assert not uraiden_instance.call().trusted_contracts(A)

    txn_hash = uraiden_instance.transact(
        {'from': owner}
    ).addTrustedContracts([trusted_contract1.address])
    assert uraiden_instance.call().trusted_contracts(trusted_contract1.address)

    print_gas(txn_hash, 'add 1 trusted contract')

    txn_hash = uraiden_instance.transact({'from': owner}).addTrustedContracts([
        trusted_contract2.address,
        trusted_contract3.address,
        A,
        trusted_contract4.address
    ])
    assert uraiden_instance.call().trusted_contracts(trusted_contract2.address)
    assert uraiden_instance.call().trusted_contracts(trusted_contract3.address)
    assert uraiden_instance.call().trusted_contracts(trusted_contract4.address)
    assert not uraiden_instance.call().trusted_contracts(A)

    print_gas(txn_hash, 'add 3 trusted contracts')


def test_add_trusted_contracts_event(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract,
        event_handler
):
    (A, B) = get_accounts(2)
    ev_handler = event_handler(uraiden_instance)
    trusted_contract = delegate_contract()

    txn_hash = uraiden_instance.transact({'from': owner}).addTrustedContracts(
        [trusted_contract.address]
    )

    ev_handler.add(
        txn_hash,
        URAIDEN_EVENTS['trusted'],
        checkTrustedEvent(trusted_contract.address, True)
    )
    ev_handler.check()


def test_remove_trusted_contracts_call(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract
):
    (A, B) = get_accounts(2)
    trusted_contract1 = delegate_contract()
    trusted_contract2 = delegate_contract()

    uraiden_instance.transact({'from': owner}).addTrustedContracts(
        [trusted_contract1.address, trusted_contract2.address]
    )

    with pytest.raises(TypeError):
        uraiden_instance.transact({'from': owner}).removeTrustedContracts([FAKE_ADDRESS])

    uraiden_instance.transact({'from': owner}).removeTrustedContracts([])
    uraiden_instance.transact({'from': owner}).removeTrustedContracts(
        [EMPTY_ADDRESS, trusted_contract1.address]
    )


def test_remove_trusted_contracts_only_owner(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract
):
    (A, B) = get_accounts(2)
    trusted_contract = delegate_contract()

    uraiden_instance.transact({'from': owner}).addTrustedContracts([trusted_contract.address])
    assert uraiden_instance.call().trusted_contracts(trusted_contract.address)

    with pytest.raises(tester.TransactionFailed):
        uraiden_instance.transact({'from': A}).removeTrustedContracts([trusted_contract.address])

    uraiden_instance.transact({'from': owner}).removeTrustedContracts(
        [trusted_contract.address]
    )
    assert not uraiden_instance.call().trusted_contracts(trusted_contract.address)


def test_remove_trusted_contracts_state(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract,
        print_gas
):
    (A, B) = get_accounts(2)
    trusted_contract1 = delegate_contract()
    trusted_contract2 = delegate_contract()
    trusted_contract3 = delegate_contract()

    uraiden_instance.transact({'from': owner}).addTrustedContracts([
        trusted_contract1.address,
        trusted_contract2.address,
        trusted_contract3.address
    ])

    assert uraiden_instance.call().trusted_contracts(trusted_contract1.address)
    assert uraiden_instance.call().trusted_contracts(trusted_contract2.address)
    assert uraiden_instance.call().trusted_contracts(trusted_contract3.address)

    txn_hash = uraiden_instance.transact({'from': owner}).removeTrustedContracts([
        trusted_contract1.address,
        trusted_contract2.address,
        A
    ])
    assert not uraiden_instance.call().trusted_contracts(trusted_contract1.address)
    assert not uraiden_instance.call().trusted_contracts(trusted_contract2.address)
    assert uraiden_instance.call().trusted_contracts(trusted_contract3.address)

    print_gas(txn_hash, 'remove 3 trusted contracts')

    txn_hash = uraiden_instance.transact({'from': owner}).removeTrustedContracts([
        trusted_contract3.address
    ])

    assert not uraiden_instance.call().trusted_contracts(trusted_contract3.address)

    print_gas(txn_hash, 'remove 1 trusted contract')


def test_remove_trusted_contracts_event(
        owner,
        get_accounts,
        uraiden_instance,
        delegate_contract,
        event_handler
):
    (A, B) = get_accounts(2)
    ev_handler = event_handler(uraiden_instance)
    trusted_contract1 = delegate_contract()
    trusted_contract2 = delegate_contract()

    uraiden_instance.transact({'from': owner}).addTrustedContracts(
        [trusted_contract1.address, trusted_contract2.address]
    )

    txn_hash = uraiden_instance.transact({'from': owner}).removeTrustedContracts(
        [trusted_contract1.address]
    )

    ev_handler.add(
        txn_hash,
        URAIDEN_EVENTS['trusted'],
        checkTrustedEvent(trusted_contract1.address, False)
    )
    ev_handler.check()

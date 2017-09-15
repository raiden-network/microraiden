import pytest
from ethereum import tester
from fixtures import (
    create_contract,
    token_contract,
)


def test_token_mint(web3, token_contract):
    token = token_contract([10000, "ERC223Token", 18, "TKN"])
    (A, B) = web3.eth.accounts[1:3]

    supply = token.call().totalSupply()

    with pytest.raises(TypeError):
        token.transact({'from': A}).mint(-3)

    with pytest.raises(tester.TransactionFailed):
        token.transact({'from': A}).mint(10001)

    token.transact({'from': A}).mint(500)
    assert token.call().balanceOf(A) == 500
    assert token.call().totalSupply() == supply + 500

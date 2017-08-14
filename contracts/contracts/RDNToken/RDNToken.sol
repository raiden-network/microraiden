/*
This Token Contract implements the standard token functionality (https://github.com/ethereum/EIPs/issues/20) as well as the following OPTIONAL extras intended for use by humans.

In other words. This is intended for deployment in something like a Token Factory or Mist wallet, and then used by humans.
Imagine coins, currencies, shares, voting weight, etc.
Machine-based, rapid creation of many tokens would not necessarily need these extra features or will be minted in other manners.

1) Initial Finite Supply (upon creation one specifies how much is minted).
2) In the absence of a token registry: Optional Decimal, Symbol & Name.
3) Optional approveAndCall() functionality to notify a contract if an approval() has occurred.

.*/

import "./StandardToken.sol";
import "./ContractReceiver.sol";

pragma solidity ^0.4.8;

contract RDNToken is StandardToken {

    /* Public variables of the token */

    address public owner;

    /*
    NOTE:
    The following variables are OPTIONAL vanities. One does not have to include them.
    They allow one to customise the token contract & in no way influences the core functionality.
    Some wallets/interfaces might not even bother to look at this information.
    */
    string public version = 'H0.1';       //human 0.1 standard. Just an arbitrary versioning scheme.

    function RDNToken (
        uint256 _initialAmount,
        string _tokenName,
        uint8 _decimalUnits,
        string _tokenSymbol
        )
    {
        owner = msg.sender;
        balances[owner] = _initialAmount;               // Give the creator all initial tokens
        totalSupply = _initialAmount;                        // Update total supply
        name = _tokenName;                                   // Set the name for display purposes
        decimals = _decimalUnits;                            // Amount of decimals for display purposes
        symbol = _tokenSymbol;                               // Set the symbol for display purposes
    }

    function isContractTrusted(
        address _addr)
        public
        returns (bool)
    {
        require(_addr != 0x0);
        ContractReceiver receiver = ContractReceiver(_addr);
        require(receiver.owner() == owner);
        return true;
    }
}

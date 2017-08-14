/*
You should inherit from StandardToken.
(This implements ONLY the standard functions and NOTHING else.
If you deploy this, you won't have anything useful.)

Implements ERC 223 Token standard: https://github.com/ethereum/EIPs/issues/223
.*/
pragma solidity ^0.4.11;

import "./Token.sol";
import "./SafeMath.sol";
import "./ERC223ReceivingContract.sol";

/// @title Standard token contract - Standard token implementation.
contract StandardToken is Token {
    using SafeMath for uint256;

    mapping(address => uint256) balances;

    /*
     *  Public functions
     */

    /// @dev Function that is called when a user or another contract wants to transfer funds.
    /// @param to Address of token receiver.
    /// @param value Number of tokens to transfer.
    /// @param data Data to be sent to tokenFallback
    /// @return Returns success of function call.
    function transfer(address to, uint256 value, bytes data)
        returns (bool)
    {
        // Standard function transfer similar to ERC20 transfer with no _data .
        // Added due to backwards compatibility reasons .
        uint256 codeLength;

        assembly {
            // Retrieve the size of the code on target address, this needs assembly .
            codeLength := extcodesize(to)
        }

        balances[msg.sender] = balances[msg.sender].sub(value);
        balances[to] = balances[to].add(value);
        if(codeLength>0) {
            ERC223ReceivingContract receiver = ERC223ReceivingContract(to);
            receiver.tokenFallback(msg.sender, value, data);
        }
        Transfer(msg.sender, to, value, data);
        return true;
    }

    /// @dev Standard function transfer similar to ERC20 transfer with no _data, added due to backwards compatibility reasons.
    /// @param to Address of token receiver.
    /// @param value Number of tokens to transfer.
    /// @return Returns success of function call.
    function transfer(address to, uint256 value)
        returns (bool)
    {
        uint256 codeLength;

        assembly {
            // Retrieve the size of the code on target address, this needs assembly .
            codeLength := extcodesize(to)
        }

        balances[msg.sender] = balances[msg.sender].sub(value);
        balances[to] = balances[to].add(value);
        if(codeLength>0) {
            ERC223ReceivingContract receiver = ERC223ReceivingContract(to);
            bytes memory empty;
            receiver.tokenFallback(msg.sender, value, empty);
        }
        Transfer(msg.sender, to, value, empty);
        return true;
    }

    // @dev Returns number of tokens owned by given address.
    /// @param _owner Address of token owner.
    /// @return Returns balance of owner.
    function balanceOf(address _owner)
        constant
        public
        returns (uint256)
    {
        return balances[_owner];
    }
}

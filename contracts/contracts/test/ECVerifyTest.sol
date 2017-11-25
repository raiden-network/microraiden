pragma solidity ^0.4.17;

/*
This is a contract used for testing the ECVerify library and ecrecover behaviour.
.*/

import "../lib/ECVerify.sol";

contract ECVerifyTest {
    function verify(
        bytes32 _message,
        bytes _signed_message)
        public
        constant
        returns (address)
    {
        // Derive address from signature
        address signer = ECVerify.ecverify(_message, _signed_message);
        return signer;
    }

    function verify_ecrecover_output(
        bytes32 hash,
        bytes32 r,
        bytes32 s,
        uint8 v)
        returns (address signature_address)
    {
        signature_address = ecrecover(hash, v, r, s);

        // ecrecover returns zero on error
        require(signature_address != 0x0);

        return signature_address;
    }

    function verifyEthSignedTypedData(
        address _address,
        uint32 _value,
        uint192 _value2,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        // The hashed strings should be kept in sync with this function's parameters
        // (variable names and types)
        var hash = keccak256(
          keccak256('address Address', 'uint32 Value', 'uint192 Value2'),
          keccak256(_address, _value, _value2)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }
}

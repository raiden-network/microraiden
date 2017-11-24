pragma solidity ^0.4.17;

import "../lib/ECVerify.sol";

contract ECVerifyTest {
    function verify(
        string _prefixed_message,
        bytes _signed_message)
        public
        constant
        returns (address)
    {
        // Hash the prefixed message string
        bytes32 prefixed_message_hash = keccak256(_prefixed_message);

        // Derive address from signature
        address signer = ECVerify.ecverify(prefixed_message_hash, _signed_message);
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

    function verifyEthSignedTypedDataString(
        string _value,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('string Message'),
          keccak256(_value)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }

    function verifyEthSignedTypedDataUint(
        uint _value,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('uint Value'),
          keccak256(_value)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }

    function verifyEthSignedTypedDataAddress(
        address _address,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('address Address'),
          keccak256(_address)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }

    function verifyEthSignedTypedDataStringUint(
        string _message,
        uint _value,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('string Message', 'uint Value'),
          keccak256(_message, _value)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }

    function verifyEthSignedTypedDataAddressStringUint(
        address _address,
        string _message,
        uint _value,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('address Address', 'string Message', 'uint Value'),
          keccak256(_address, _message, _value)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }

    function verifyEthSignedTypedDataAddressUintUint(
        address _address,
        uint32 _value,
        uint192 _value2,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        var hash = keccak256(
          keccak256('address Address', 'uint32 Value', 'uint192 Value2'),
          keccak256(_address, _value, _value2)
        );

        // Derive address from signature
        address signer = ECVerify.ecverify(hash, _balance_msg_sig);
        return signer;
    }
}

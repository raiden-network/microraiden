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
}

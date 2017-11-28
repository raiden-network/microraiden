pragma solidity ^0.4.17;

contract MicroRaidenEIP712Helper {
    /// @dev Returns the message hash used for creating the balance proof.
    /// Used in the RaidenMicroTransferChannels contract.
    /// Should be kept up-to-date with eth_signTypedData https://github.com/ethereum/EIPs/pull/712.
    /// @param _receiver_address The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the
    /// sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @param _contract RaidenMicroTransferChannels contract address
    /// @return Hash of the message composed from the above parameters.
    function getMessageHash(
        address _receiver_address,
        uint32 _open_block_number,
        uint192 _balance,
        address _contract)
        public
        pure
        returns (bytes32)
    {
        // The variable names from below will be shown to the sender when signing
        // the balance proof, so they have to be kept in sync with the Dapp client.
        // The hashed strings should be kept in sync with this function's parameters
        // (variable names and types)
        bytes32 message_hash = keccak256(
          keccak256('address receiver', 'uint32 block_created', 'uint192 balance', 'address contract'),
          keccak256(_receiver_address, _open_block_number, _balance, _contract)
        );

        return message_hash;
    }
}

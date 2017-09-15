pragma solidity ^0.4.11;

import "./Token/Token.sol";
import "./lib/ECVerify.sol";

/// @title Raiden MicroTransfer Channels Contract.
contract RaidenMicroTransferChannels {

    /*
     *  Data structures
     */

    address public owner;
    address public token_address;
    uint8 public challenge_period;
    string constant prefix = "\x19Ethereum Signed Message:\n";

    Token token;

    mapping (bytes32 => Channel) channels;
    mapping (bytes32 => ClosingRequest) closing_requests;

    // 28 (deposit) + 4 (block no settlement)
    struct Channel {
        uint192 deposit; // mAX 2^192 == 2^6 * 2^18
        uint32 open_block_number; // UNIQUE for participants to prevent replay of messages in later channels
    }

    struct ClosingRequest {
        uint32 settle_block_number;
        uint192 closing_balance;
    }

    /*
     *  Modifiers
     */

    modifier isToken() {
        require(msg.sender == token_address);
        _;
    }

    /*
     *  Events
     */

    event ChannelCreated(
        address indexed _sender,
        address indexed _receiver,
        uint192 _deposit);
    event ChannelToppedUp (
        address indexed _sender,
        address indexed _receiver,
        uint32 indexed _open_block_number,
        uint192 _added_deposit,
        uint192 _deposit);
    event ChannelCloseRequested(
        address indexed _sender,
        address indexed _receiver,
        uint32 indexed _open_block_number,
        uint192 _balance);
    event ChannelSettled(
        address indexed _sender,
        address indexed _receiver,
        uint32 indexed _open_block_number,
        uint192 _balance);
    event GasCost(
        string _function_name,
        uint _gaslimit,
        uint _gas_remaining);

    /*
     *  Constructor
     */

    /// @dev Constructor for creating the Raiden microtransfer channels contract.
    /// @param _token The address of the Token used by the channels.
    /// @param _challenge_period A fixed number of blocks representing the challenge period after a sender requests the closing of the channel without the receiver's signature.
    function RaidenMicroTransferChannels(address _token, uint8 _challenge_period) {
        require(_token != 0x0);
        require(_challenge_period > 0);

        owner = msg.sender;
        token_address = _token;
        token = Token(_token);

        challenge_period = _challenge_period;
    }

    /*
     *  Public helper functions (constant)
     */

    /// @dev Returns the unique channel identifier used in the contract.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @return Unique channel identifier.
    function getKey(
        address _sender,
        address _receiver,
        uint32 _open_block_number)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_sender, _receiver, _open_block_number);
    }

    /// @dev Returns a hash of the balance message needed to be signed by the sender.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @return Hash of the balance message.
    function getBalanceMessage(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance)
        public
        constant
        returns (string)
    {
        string memory str = concat("Receiver: 0x", addressToString(_receiver));
        str = concat(str, ", Balance: ");
        str = concat(str, uintToString(uint256(_balance)));
        str = concat(str, ", Channel ID: ");
        str = concat(str, uintToString(uint256(_open_block_number)));
        return str;
    }

    // 56014 gas cost
    /// @dev Returns the sender address extracted from the balance proof.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @param _balance_msg_sig The balance message signed by the sender or receiver.
    /// @return Address of the balance proof signer.
    function verifyBalanceProof(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        //GasCost('close verifyBalanceProof getBalanceMessage start', block.gaslimit, msg.gas);
        // Create message which should be signed by sender
        string memory message = getBalanceMessage(_receiver, _open_block_number, _balance);
        //GasCost('close verifyBalanceProof getBalanceMessage end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof length start', block.gaslimit, msg.gas);
        // 2446 gas cost
        // TODO: improve length calc
        uint message_length = bytes(message).length;
        //GasCost('close verifyBalanceProof length end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof uintToString start', block.gaslimit, msg.gas);
        string memory message_length_string = uintToString(message_length);
        //GasCost('close verifyBalanceProof uintToString end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof concat start', block.gaslimit, msg.gas);
        // Prefix the message
        string memory prefixed_message = concat(prefix, message_length_string);
        //GasCost('close verifyBalanceProof concat end', block.gaslimit, msg.gas);

        prefixed_message = concat(prefixed_message, message);


        // Hash the prefixed message string
        bytes32 prefixed_message_hash = sha3(prefixed_message);

        // Derive address from signature
        address signer = ECVerify.ecverify(prefixed_message_hash, _balance_msg_sig);
        return signer;
    }

    /*
     *  External functions
     */

    /// @dev Calls createChannel, compatibility with ERC 223; msg.sender is Token contract.
    /// @param _sender The address that sends the tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    /// @param _data Receiver address in bytes.
    function tokenFallback(
        address _sender,
        uint256 _deposit,
        bytes _data)
        external
    {
        // Make sure we trust the token
        require(msg.sender == token_address);
        //GasCost('tokenFallback start0', block.gaslimit, msg.gas);
        uint length = _data.length;

        // createChannel - receiver address (20 bytes + padding = 32 bytes)
        // topUp - receiver address (32 bytes) + open_block_number (4 bytes + padding = 32 bytes)
        require(length == 20 || length == 24);
        //GasCost('tokenFallback addressFromData start', block.gaslimit, msg.gas);
        address receiver = addressFromData(_data);
        //GasCost('tokenFallback addressFromData end', block.gaslimit, msg.gas);

        if(length == 20) {
            createChannelPrivate(_sender, receiver, uint192(_deposit));
        }
        else {
            //GasCost('tokenFallback blockNumberFromData start', block.gaslimit, msg.gas);
            uint32 open_block_number = blockNumberFromData(_data);
            //GasCost('tokenFallback blockNumberFromData end', block.gaslimit, msg.gas);
            topUpPrivate(_sender, receiver, open_block_number, uint192(_deposit));
        }
        //GasCost('tokenFallback end', block.gaslimit, msg.gas);
    }

    /// @dev Creates a new channel between a sender and a receiver and transfers the sender's token deposit to this contract, compatibility with ERC20 tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    function createChannelERC20(
        address _receiver,
        uint192 _deposit)
        external
    {
        createChannelPrivate(msg.sender, _receiver, _deposit);

        // transferFrom deposit from _sender to contract
        // ! needs prior approval from user
        require(token.transferFrom(msg.sender, address(this), _deposit));
    }

    // TODO (WIP) Funds channel with an additional deposit of tokens. ERC20 compatibility.
    /// @dev Increase the sender's current deposit.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _added_deposit The added token deposit with which the current deposit is increased.
    function topUpERC20(
        address _receiver,
        uint32 _open_block_number,
        uint192 _added_deposit)
        external
    {
        // transferFrom deposit from msg.sender to contract
        // ! needs prior approval from user
        require(token.transferFrom(msg.sender, address(this), _added_deposit));
        topUpPrivate(msg.sender, _receiver, _open_block_number, _added_deposit);
    }

    /// @dev Function called when any of the parties wants to close the channel and settle; receiver needs a balance proof to immediately settle, sender triggers a challenge period.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @param _balance_msg_sig The balance message signed by the sender.
    function close(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance,
        bytes _balance_msg_sig)
        external
    {
        require(_balance_msg_sig.length == 65);
        //GasCost('close verifyBalanceProof start', block.gaslimit, msg.gas);
        address sender = verifyBalanceProof(_receiver, _open_block_number, _balance, _balance_msg_sig);
        //GasCost('close verifyBalanceProof end', block.gaslimit, msg.gas);

        if(msg.sender == _receiver) {
            settleChannel(sender, _receiver, _open_block_number, _balance);
        }
        else {
            require(msg.sender == sender);
            initChallengePeriod(_receiver, _open_block_number, _balance);
        }
    }

    /// @dev Function called by the sender, when he has a closing signature from the receiver; channel is closed immediately.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @param _balance_msg_sig The balance message signed by the sender.
    /// @param _closing_sig The hash of the signed balance message, signed by the receiver.
    function close(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance,
        bytes _balance_msg_sig,
        bytes _closing_sig)
        external
    {
        require(_balance_msg_sig.length == 65);
        require(_closing_sig.length == 65);

        //GasCost('close coop verifyBalanceProof start', block.gaslimit, msg.gas);
        // derive address from signature
        address receiver = verifyBalanceProof(_receiver, _open_block_number, _balance, _closing_sig);
        //GasCost('close coop verifyBalanceProof start', block.gaslimit, msg.gas);

        require(receiver == _receiver);

        address sender = verifyBalanceProof(_receiver, _open_block_number, _balance, _balance_msg_sig);
        require(msg.sender == sender);
        settleChannel(sender, receiver, _open_block_number, _balance);
    }

    /// @dev Function for getting information about a channel.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @return Channel information (unique_identifier, deposit, settle_block_number, closing_balance).
    function getChannelInfo(
        address _sender,
        address _receiver,
        uint32 _open_block_number)
        external
        constant
        returns (bytes32, uint192, uint32, uint192)
    {
        bytes32 key = getKey(_sender, _receiver, _open_block_number);
        require(channels[key].open_block_number != 0);

        return (key, channels[key].deposit, closing_requests[key].settle_block_number, closing_requests[key].closing_balance);
    }

    /// @dev Function called by the sender after the challenge period has ended, in case the receiver has not closed the channel.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    function settle(
        address _receiver,
        uint32 _open_block_number)
        external
    {
        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(closing_requests[key].settle_block_number != 0);
	    require(block.number > closing_requests[key].settle_block_number);

        settleChannel(msg.sender, _receiver, _open_block_number, closing_requests[key].closing_balance);
    }

    /*
     *  Private functions
     */

    /// @dev Creates a new channel between a sender and a receiver, only callable by the Token contract.
    /// @param _sender The address that receives tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    function createChannelPrivate(
        address _sender,
        address _receiver,
        uint192 _deposit)
        private
    {
        //GasCost('createChannel start', block.gaslimit, msg.gas);
        uint32 open_block_number = uint32(block.number);

        // Create unique identifier from sender, receiver and current block number
        bytes32 key = getKey(_sender, _receiver, open_block_number);

        require(channels[key].deposit == 0);
        require(channels[key].open_block_number == 0);
        require(closing_requests[key].settle_block_number == 0);

        // Store channel information
        channels[key] = Channel({deposit: _deposit, open_block_number: open_block_number});
        //GasCost('createChannel end', block.gaslimit, msg.gas);
        ChannelCreated(_sender, _receiver, _deposit);
    }

    // TODO (WIP)
    /// @dev Funds channel with an additional deposit of tokens, only callable by the Token contract.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _added_deposit The added token deposit with which the current deposit is increased.
    function topUpPrivate(
        address _sender,
        address _receiver,
        uint32 _open_block_number,
        uint192 _added_deposit)
        private
    {
        //GasCost('topUp start', block.gaslimit, msg.gas);
        require(_added_deposit != 0);
        require(_open_block_number != 0);

        bytes32 key = getKey(_sender, _receiver, _open_block_number);

        require(channels[key].deposit != 0);
        require(closing_requests[key].settle_block_number == 0);

        channels[key].deposit += _added_deposit;
        ChannelToppedUp(_sender, _receiver, _open_block_number, _added_deposit, channels[key].deposit);
        //GasCost('topUp end', block.gaslimit, msg.gas);
    }


    /// @dev Sender starts the challenge period; this can only happend once.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    function initChallengePeriod(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance)
        private
    {
        //GasCost('initChallengePeriod end', block.gaslimit, msg.gas);
        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(closing_requests[key].settle_block_number == 0);
        require(_balance <= channels[key].deposit);

        // Mark channel as closed
        closing_requests[key].settle_block_number = uint32(block.number) + challenge_period;
        closing_requests[key].closing_balance = _balance;
        ChannelCloseRequested(msg.sender, _receiver, _open_block_number, _balance);
        //GasCost('initChallengePeriod end', block.gaslimit, msg.gas);
    }

    /// @dev Closes the channel and settles by transfering the balance to the receiver and the rest of the deposit back to the sender.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    function settleChannel(
        address _sender,
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance)
        private
    {
        //GasCost('settleChannel start', block.gaslimit, msg.gas);
        bytes32 key = getKey(_sender, _receiver, _open_block_number);
        Channel channel = channels[key];

        // TODO delete this if we don't include open_block_number in the Channel struct
        require(channel.open_block_number != 0);
        require(_balance <= channel.deposit);

        // send minimum of _balance and deposit to receiver
        uint send_to_receiver = min(_balance, channel.deposit);
        if(send_to_receiver > 0) {
            //GasCost('settleChannel', block.gaslimit, msg.gas);
            require(token.transfer(_receiver, send_to_receiver));
        }

        // send maximum of deposit - balance and 0 to sender
        uint send_to_sender = max(channel.deposit - _balance, 0);
        if(send_to_sender > 0) {
            //GasCost('settleChannel', block.gaslimit, msg.gas);
            require(token.transfer(_sender, send_to_sender));
        }

        assert(channel.deposit >= _balance);

        // remove closed channel structures
        delete channels[key];
        delete closing_requests[key];

        ChannelSettled(_sender, _receiver, _open_block_number, _balance);
        //GasCost('settleChannel end', block.gaslimit, msg.gas);
    }

    /*
     *  Internal functions
     */

    /// @dev Internal function for getting the maximum between two numbers.
    /// @param a First number to compare.
    /// @param b Second number to compare.
    /// @return The maximum between the two provided numbers.
    function max(uint192 a, uint192 b)
        internal
        constant
        returns (uint)
    {
        if (a > b) return a;
        else return b;
    }

    /// @dev Internal function for getting the minimum between two numbers.
    /// @param a First number to compare.
    /// @param b Second number to compare.
    /// @return The minimum between the two provided numbers.
    function min(uint192 a, uint192 b)
        internal
        constant
        returns (uint)
    {
        if (a < b) return a;
        else return b;
    }

    // 2656 gas cost
    /// @dev Internal function for getting an address from tokenFallback data bytes.
    /// @param b Bytes received.
    /// @return Address resulted.
    function addressFromData (
        bytes b)
        internal
        constant
        returns (address)
    {
        bytes20 addr;
        assembly {
            // Read address bytes
            // Offset of 32 bytes, representing b.length
            addr := mload(add(b, 0x20))
        }
        return address(addr);
    }

    // 2662 gas cost
    /// @dev Internal function for getting the block number from tokenFallback data bytes.
    /// @param b Bytes received.
    /// @return Block number.
    function blockNumberFromData(
        bytes b)
        internal
        constant
        returns (uint32)
    {
        bytes4 block_number;
        assembly {
            // Read block number bytes
            // Offset of 32 bytes (b.length) + 20 bytes (address)
            block_number := mload(add(b, 0x34))
        }
        return uint32(block_number);
    }

    function memcpy(
        uint dest,
        uint src,
        uint len)
        private
    {
        // Copy word-length chunks while possible
        for(; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }

        // Copy remaining bytes
        uint mask = 256 ** (32 - len) - 1;
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    // 3813 gas cost
    function concat(
        string _self,
        string _other)
        internal
        constant
        returns (string)
    {
        uint self_len = bytes(_self).length;
        uint other_len = bytes(_other).length;
        uint self_ptr;
        uint other_ptr;

        assembly {
            self_ptr := add(_self, 0x20)
            other_ptr := add(_other, 0x20)
        }

        var ret = new string(self_len + other_len);
        uint retptr;
        assembly { retptr := add(ret, 32) }
        memcpy(retptr, self_ptr, self_len);
        memcpy(retptr + self_len, other_ptr, other_len);
        return ret;
    }

    /*function uintToBytes (
        uint256 n)
        internal
        constant
        returns (bytes32 b)
    {
        //b = new bytes(32);
        assembly {
            //mstore(add(b, 32), n)
            b := mload(add(n, 32))
        }
    }

    function uintToBytes32 (
        uint256 n)
        internal
        constant
        returns (bytes32 b)
    {
        assembly {
            b := mload(add(n, 32))
        }
    }

    function stringToBytes1(
        string str)
        internal
        constant
        returns (bytes)
    {
        return bytes(str);
    }

    function stringToBytes2(
        string source)
        internal
        constant
        returns (bytes result)
    {
        uint len = bytes(source).length;
        result = new bytes(len);
        assembly {
            result := mload(add(source, len))
        }
    }*/

    // 9613 gas
    function uintToString(
        uint v)
        internal
        constant
        returns (string)
    {
        bytes32 ret;
        if (v == 0) {
            ret = '0';
        }
        else {
             while (v > 0) {
                ret = bytes32(uint(ret) / (2 ** 8));
                ret |= bytes32(((v % 10) + 48) * 2 ** (8 * 31));
                v /= 10;
            }
        }

        bytes memory bytesString = new bytes(32);
        uint charCount = 0;
        for (uint j=0; j<32; j++) {
            byte char = byte(bytes32(uint(ret) * 2 ** (8 * j)));
            if (char != 0) {
                bytesString[j] = char;
                charCount++;
            }
        }
        bytes memory bytesStringTrimmed = new bytes(charCount);
        for (j = 0; j < charCount; j++) {
            bytesStringTrimmed[j] = bytesString[j];
        }

        return string(bytesStringTrimmed);
    }

    function addressToString(
        address x)
        internal
        constant
        returns (string)
    {
        bytes memory str = new bytes(40);
        for (uint i = 0; i < 20; i++) {
            byte b = byte(uint8(uint(x) / (2**(8*(19 - i)))));
            byte hi = byte(uint8(b) / 16);
            byte lo = byte(uint8(b) - 16 * uint8(hi));
            str[2*i] = char(hi);
            str[2*i+1] = char(lo);
        }
        return string(str);
    }

    function char(byte b)
        internal
        constant
        returns (byte c)
    {
        if (b < 10) return byte(uint8(b) + 0x30);
        else return byte(uint8(b) + 0x57);
    }
}

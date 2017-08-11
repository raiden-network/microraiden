pragma solidity ^0.4.11;

import "./RDNToken/Token.sol";
import "./lib/ECVerify.sol";

/// @title Raiden MicroTransfer Channels Contract.
contract RaidenMicroTransferChannels {

    /*
     *  Data structures
     */

    address public token_address;
    uint8 public challenge_period;

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
     *  Events
     */

    event ChannelCreated(address indexed _sender, address indexed _receiver, uint192 _deposit);
    event ChannelTopedUp (address _sender, address _receiver, uint32 _open_block_number, uint192 _added_depozit, uint192 _depozit);
    event ChannelCloseRequested(address indexed _sender, address indexed _receiver, uint32 _open_block_number, uint192 _balance);
    event ChannelSettled(address indexed _sender, address indexed _receiver, uint32 _open_block_number);

    /*
     *  Constructor
     */

    /// @dev Constructor for creating the Raiden microtransfer channels contract.
    /// @param _token The address of the Token used by the channels.
    /// @param _challenge_period A fixed number of blocks representing the challenge period after a sender requests the closing of the channel without the receiver's signature.
    function RaidenMicroTransferChannels(address _token, uint8 _challenge_period) {
        require(_token != 0x0);
        require(_challenge_period > 0);
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
    function balanceMessageHash(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_receiver, _open_block_number, _balance, address(this));
    }

    /// @dev Returns a hash of the balance message that was signed by the sender, so it can be subsequently signed by the receiver.
    /// @param _balance_msg_sig The balance message signed by the sender.
    /// @return Hash of the balance message signed by the sender.
    function closingAgreementMessageHash(bytes _balance_msg_sig)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_balance_msg_sig);
    }

    /// @dev Returns the sender address extracted from the balance proof.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    /// @param _balance_msg_sig The balance message signed by the sender.
    /// @return Address of the token sender.
    function verifyBalanceProof(
        address _receiver,
        uint32 _open_block_number,
        uint192 _balance,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        // Create message which should be signed by sender
        bytes32 message = balanceMessageHash(_receiver, _open_block_number, _balance);
        // Derive address from signature
        address sender = ECVerify.ecverify(message, _balance_msg_sig);
        return sender;
    }

    /// @dev Returns the receiver address extracted from the closing signature and the signed balance message.
    /// @param _balance_msg_sig The balance message signed by the sender.
    /// @param _closing_sig The hash of the signed balance message, signed by the receiver.
    /// @return Address of the tokens receiver.
    function verifyClosingSignature(
        bytes _balance_msg_sig,
        bytes _closing_sig)
        public
        constant
        returns (address)
    {
        bytes32 balance_msg_sig_hash = closingAgreementMessageHash(_balance_msg_sig);
        address receiver = ECVerify.ecverify(balance_msg_sig_hash, _closing_sig);
        return receiver;
    }

    /*
     *  External functions
     */

    /// @dev Creates a new channel between a sender and a receiver and transfers the sender's token deposit to this contract.
    /// @param _receiver The address that receives tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    function createChannel(
        address _receiver,
        uint192 _deposit)
        external
    {
        uint32 open_block_number = uint32(block.number);

        // Create unique identifier from sender, receiver and current block number
        bytes32 key = getKey(msg.sender, _receiver, open_block_number);

        require(channels[key].deposit == 0);
        require(channels[key].open_block_number == 0);
        require(closing_requests[key].settle_block_number == 0);

        // Store channel information
        channels[key] = Channel({deposit: _deposit, open_block_number: open_block_number});

        // transferFrom deposit from msg.sender to contract
        // ! needs prior approval from user
        require(token.transferFrom(msg.sender, address(this), _deposit));
        ChannelCreated(msg.sender, _receiver, _deposit);
    }

    // TODO (WIP) Funds channel with an additional depozit of tokens
    /// @dev Increase the sender's current depozit.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _added_deposit The added token deposit with which the current deposit is increased.
    function topUp(
        address _receiver,
        uint32 _open_block_number,
        uint192 _added_deposit)
        external
    {
        require(_added_deposit != 0);
        require(_open_block_number != 0);

        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(channels[key].deposit != 0);
        require(closing_requests[key].settle_block_number == 0);

        // transferFrom deposit from msg.sender to contract
        // ! needs prior approval from user
        require(token.transferFrom(msg.sender, address(this), _added_deposit));

        channels[key].deposit += _added_deposit;
        ChannelTopedUp(msg.sender, _receiver, _open_block_number, _added_deposit, channels[key].deposit);
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
        address sender = verifyBalanceProof(_receiver, _open_block_number, _balance, _balance_msg_sig);

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
        // derive address from signature
        address receiver = verifyClosingSignature(_balance_msg_sig, _closing_sig);
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
        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(closing_requests[key].settle_block_number == 0);

        // Mark channel as closed
        closing_requests[key].settle_block_number = uint32(block.number) + challenge_period;
        closing_requests[key].closing_balance = _balance;
        ChannelCloseRequested(msg.sender, _receiver, _open_block_number, _balance);
    }

    /// @dev Closes the channel and settles by transfering the balance to the receiver and the rest of the depozit back to the sender.
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
        bytes32 key = getKey(_sender, _receiver, _open_block_number);
        Channel channel = channels[key];

        // TODO delete this if we don't include open_block_number in the Channel struct
        require(channel.open_block_number != 0);

        // send minimum of _balance and deposit to receiver
        uint send_to_receiver = min(_balance, channel.deposit);
        require(token.transfer(_receiver, send_to_receiver));

        // send maximum of deposit - balance and 0 to sender
        uint send_to_sender = max(channel.deposit - _balance, 0);
        require(token.transfer(_sender, send_to_sender));

        assert(channel.deposit >= _balance);

        // remove closed channel structures
        delete channels[key];
        delete closing_requests[key];

        ChannelSettled(_sender, _receiver, _open_block_number);
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
}

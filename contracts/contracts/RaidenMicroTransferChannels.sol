pragma solidity ^0.4.11;

import "./RDNToken/Token.sol";
import "./lib/ECVerify.sol";

// TODO There is only one channel sender > receiver with a contract at a time

/// @title RaidenMicroTransferChannels - Standard token implementation.
contract RaidenMicroTransferChannels {

    /*
     *  Data structures
     */

    address public token_address;
    uint8 public challenge_period;

    mapping (bytes32 => Channel) channels;
    mapping (bytes32 => ClosingRequest) closing_requests;

    // 28 (deposit) + 4 (block no settlement)
    struct Channel {
        uint192 deposit; // mAX 2^192 == 2^6 * 2^18
        uint32 open_block_number; // UNIQUE for participants to prevent replay of messages in later channels
    }

    struct ClosingRequest {
        uint32 settle_block_number;
        uint32 closing_balance;
    }

    /*
     *  Events
     */

    event ChannelCreated(address indexed _sender, address indexed _receiver, uint32 _deposit);
    event ChannelTopedUp (address _sender, address _receiver, uint32 _open_block_number, uint192 _added_depozit, uint192 _depozit);
    event ChannelCloseRequested(address indexed _sender, address indexed _receiver, uint32 _open_block_number, uint32 _balance);
    event ChannelSettled(address indexed _sender, address indexed _receiver, uint32 _open_block_number);

    /*
     *  Init function
     */

    function RaidenMicroTransferChannels(address _token, uint8 _challenge_period) {
        require(_token != 0x0);
        require(_challenge_period > 0);
        token_address = _token;
        challenge_period = _challenge_period;
    }

    /*
     *  Public helper functions (constant)
     */

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

    function balanceMessageHash(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_receiver, _open_block_number, _balance, address(this));
    }

    function closingAgreementMessageHash(bytes _balance_msg_sig)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_balance_msg_sig);
    }

    function verifyBalanceProof(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        // create message which should be signed by sender
        bytes32 message = balanceMessageHash(_receiver, _open_block_number, _balance);
        // derive address from signature
        address sender = ECVerify.ecverify(message, _balance_msg_sig);
        return sender;
    }

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

    function createChannel(
        address _receiver,
        uint32 _deposit)
        external
    {
        // create id from sender, receiver and current block number
        uint32 open_block_number = uint32(block.number);
        bytes32 key = getKey(msg.sender, _receiver, open_block_number);

        // require(channels[key] != Channel(0,0)); // Operator != not compatible with types struct
        require(channels[key].deposit == 0);
        require(channels[key].open_block_number == 0);
        require(closing_requests[key].settle_block_number == 0);

        // store channel information
        channels[key] = Channel({deposit: _deposit, open_block_number: open_block_number});

        // transferFrom deposit from msg.sender to contract
        // ! needs prior approval from user
        require(Token(token_address).transferFrom(msg.sender, address(this), _deposit));
        ChannelCreated(msg.sender, _receiver, _deposit);
    }

    // TODO (WIP) Funds channel with an additional depozit of tokens
    function topUp(
        address _receiver,
        uint32 _open_block_number,
        uint32 _added_deposit)
        external
    {
        require(_added_deposit != 0);
        require(_open_block_number != 0);

        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(channels[key].deposit != 0);
        require(closing_requests[key].settle_block_number == 0);

        channels[key].deposit += _added_deposit;
        ChannelTopedUp(msg.sender, _receiver, _open_block_number, _added_deposit, channels[key].deposit);
    }

    // Close channel and settle if called by receiver with balance proof
    // Start challenge_period if called by the sender (no receiver signature)
    function close(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance,
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

    // Called by the sender with a balance proof + receiver signature
    // Close channel and settle
    function close(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance,
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

    function getChannelInfo(
        address _sender,
        address _receiver,
        uint32 _open_block_number)
        external
        constant
        returns (bytes32, uint, uint32, uint32, uint32)
    {
        bytes32 key = getKey(_sender, _receiver, _open_block_number);
        return (key, channels[key].deposit, channels[key].open_block_number, closing_requests[key].settle_block_number, closing_requests[key].closing_balance);
    }

    // Only called by sender after the challenge_period has ended
    // Close channel and settle
    function settle(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance)
        external
    {
        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(closing_requests[key].settle_block_number != 0);
	    require(block.number > closing_requests[key].settle_block_number);

        settleChannel(msg.sender, _receiver, _open_block_number, _balance);
    }

    /*
     *  Private functions
     */

    // Only called by the sender
    // Sender can only trigger the challenge period only once
    function initChallengePeriod(
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance)
        private
    {
        bytes32 key = getKey(msg.sender, _receiver, _open_block_number);

        require(closing_requests[key].settle_block_number == 0);

        // Mark channel as closed
        closing_requests[key].settle_block_number = uint32(block.number) + challenge_period;
        ChannelCloseRequested(msg.sender, _receiver, _open_block_number, _balance);
    }

    function settleChannel(
        address _sender,
        address _receiver,
        uint32 _open_block_number,
        uint32 _balance)
        private
    {
        bytes32 key = getKey(_sender, _receiver, _open_block_number);
        Channel channel = channels[key];

        // TODO delete this if we don't include open_block_number in the Channel struct
        require(channel.open_block_number != 0);

        // send minimum of _balance and deposit to receiver
        require(Token(token_address).transfer(_receiver, min(_balance, channel.deposit)));
        // send maximum of deposit - balance and 0 to sender
        require(Token(token_address).transfer(_sender, max(channel.deposit - _balance, 0)));

        assert(channel.deposit >= _balance);
        assert(Token(token_address).balanceOf(_receiver) == min(_balance, channel.deposit));
        assert(Token(token_address).balanceOf(_sender) == max(channel.deposit - _balance, 0));

        // remove closed channel structures
        delete channels[key];
        delete closing_requests[key];

        ChannelSettled(_sender, _receiver, _open_block_number);
    }

    /*
     *  Internal functions
     */

    function max(uint a, uint b)
        internal
        constant
        returns (uint)
    {
        if (a > b) return a;
        else return b;
    }

    function min(uint a, uint b)
        internal
        constant
        returns (uint)
    {
        if (a < b) return a;
        else return b;
    }
}

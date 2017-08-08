pragma solidity ^0.4.11;

import "./RDNToken/Token.sol";
import "./lib/ECVerify.sol";

contract RaidenMicroTransferChannels {

    address token;
    uint8 challenge_period;

    // todo: indexed?
    event ChannelCreated(address indexed _sender, address indexed _receiver, uint32 indexed _deposit);
    event ChannelCloseRequested(address indexed _sender, address indexed _receiver);
    event ChannelSettled(address indexed _sender, address indexed _receiver);

    mapping (bytes32 => Channel) channels;
    // 28 (deposit) + 4 (block no settlement)
    struct Channel {
        uint192 deposit; // mAX 2^192 == 2^6 * 2^18
        uint32 close_block_number;
        uint32 open_block_number; // UNIQUE for participants to prevent replay of messages in later channels
    }

    function RaidenMicroTransferChannels(address _token, uint8 _challenge_period) {
        require(_token != 0x0);
        require(_challenge_period > 0);
        token = _token;
        challenge_period = _challenge_period;
    }

    function createChannel(address _receiver, uint32 _deposit) external {
        // create id from sender, receiver and current block number
        bytes32 key = sha3(msg.sender, _receiver, block.number);

        // require(channels[key] != Channel(0,0)); // Operator != not compatible with types struct
        require(channels[key].deposit == 0);
        require(channels[key].open_block_number == 0);
        require(channels[key].close_block_number == 0);

        // store channel information
        channels[key] = Channel({deposit: _deposit, close_block_number: 0, open_block_number: block.number});

        token.delegatecall(bytes4(sha3("approve(address,uint)")), msg.sender, _deposit);

        // transferFrom deposit from msg.sender to contract
        require(Token(token).transferFrom(msg.sender, address(this), _deposit));
        ChannelCreated(msg.sender, _receiver, _deposit);
    }

    function fundChannel(address _receiver, uint32 _deposit, uint32 _open_block_number) external {
        require(_deposit != 0);
        require(channels[key].deposit != 0);
        require(_open_block_number != 0);

        bytes32 key = sha3(msg.sender, _receiver, _open_block_number);
        channels[key].deposit += _deposit;
    }

    function close(address counterparty, uint32 _open_block_number, uint32 _balance, bytes _signature) external {
        bytes32 key = sha3(msg.sender, counterparty, _open_block_number);
        Channel channel = channels[key];

        if(channel.open_block_number > 0 && channel.open_block_number != _open_block_number) {
            key = sha3(counterparty, msg.sender, _open_block_number);
            channel = channels[key];
        }

        require(channel.open_block_number > 0);
        require(channel.open_block_number == _open_block_number);

        // is channelid valid?
        require(channel.sender != 0x0);
        // was closed not called already?
        require(channel.lastBalance == 0);
        // create message which should be signed by receiver
        // balance_proof can be sha3(channel_id, balance) signed by sender ; channel_id is unique as it also references this.address
        bytes32 message = sha3(channel.sender, channel.receiver, channel.token, _balance);
        // derive address from signature
        address signer = ECVerify.ecverify(message, _signature);
        // signer of message must be sender
        require(signer == channel.sender);
        // msg.sender must be either sender or receiver
        require((msg.sender == channel.sender) || (msg.sender == channel.receiver));

        channel.close_block_number = block.number;
        // store balance for settlement
        channel.lastBalance = _balance;
        ChannelCloseRequested(channel.sender, channel.receiver, key);
        // if called by receiver call settle immediately
        if (msg.sender == channel.receiver) {
            settle(key);
        }
    }

    // function close(address receiver) {}

    function settle(bytes32 key) public {
        Channel memory channel = channels[key];
        // is channelid valid?
        require(channel.sender != 0x0);
        // if sender is msg.sender check if challengePeriod has expired
        if (msg.sender == channel.sender) {
	        require(now > channel.challengePeriod);
        }
        // send minimum of lastBalance and deposit to receiver
        require(Token(channel.token).transfer(channel.receiver, min(channel.lastBalance, channel.deposit)));
        // send maximum of deposit - balance and 0 to sender
        require(Token(channel.token).transfer(channel.sender, max(channel.deposit - channel.lastBalance, 0)));
        // remove closed channel
        delete channels[key];
        ChannelSettled(channel.sender, channel.receiver, key);
    }

    function getChannel(address _sender, address _receiver, uint32 _open_block_number)
        external
        constant
        returns (bytes32, int, int)
    {
        bytes32 key = sha3(_sender, _receiver, _open_block_number);
        return (key, channels[key].deposit, channels[key].close_block_number);
    }

    // Helper functions
    function balanceProofHash(address _to, uint32 _value, uint32 _open_block_number)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_to, _value, address(this), _open_block_number);
    }

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

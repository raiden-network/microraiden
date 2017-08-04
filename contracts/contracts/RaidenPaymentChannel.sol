pragma solidity ^0.4.11;

import "./RDNToken/Token.sol";
import "./lib/ECVerify.sol";

contract RaidenPaymentChannel {

    event ChannelCreated(address _sender, address _receiver, bytes32 _id);
    event ChannelCloseRequested(address _sender, address _receiver, bytes32 _id);
    event ChannelSettled(address _sender, address _receiver, bytes32 _id);

    mapping (bytes32 => Channel) channels;

    struct Channel {
        address sender;
        address receiver;
        address token;
        uint32 deposit;
        uint32 lastBalance;
        uint8 challengePeriod;
    }

    function RaidenPaymentChannel() {
        // what to do here?
    }

    function init(address _receiver, address _token, uint32 _deposit, uint8 _challengePeriod) external {
        // create id from sender, receiver and token address
        bytes32 id = sha3(msg.sender, _receiver, _token);
        // store channel information
        channels[id] = Channel({sender: msg.sender, receiver: _receiver, token: _token, deposit: _deposit, challengePeriod: _challengePeriod, lastBalance: 0});
        // transferFrom deposit from msg.sender to contract
        require(Token(_token).transferFrom(msg.sender, address(this), _deposit));
        ChannelCreated(msg.sender, _receiver, id);
    }

    function close(bytes32 _id, uint32 _balance, bytes _signature) external {
        Channel channel = channels[_id];
        // is channelid valid?
        require(channel.sender != 0x0);
        // was closed not called already?
        require(channel.lastBalance == 0);
        // create message which should be signed by receiver
        bytes32 message = sha3(channel.sender, channel.receiver, channel.token, _balance);
        // derive address from signature
        address signer = ECVerify.ecverify(message, _signature);
        // signer of message must be sender
        require(signer == channel.sender);
        // msg.sender must be either sender or receiver
        require((msg.sender == channel.sender) || (msg.sender == channel.receiver));
        // store balance for settlement
        channel.lastBalance = _balance;
        ChannelCloseRequested(channel.sender, channel.receiver, _id);
        // if called by receiver call settle immediately
        if (msg.sender == channel.receiver) {
            settle(_id);
        }
    }

    function settle(bytes32 _id) public {
        Channel memory channel = channels[_id];
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
        delete channels[_id];
        ChannelSettled(channel.sender, channel.receiver, _id);
    }

    function getChannel(address _sender, address _receiver, address _token) external constant returns (bytes32, address, int, int) {
        bytes32 id = sha3(_sender, _receiver, _token);
        return (id, channels[id].token, channels[id].deposit, channels[id].challengePeriod);
    }

    // Helper functions

    function shaOfValue(address _from, address _to, address _token, uint32 _value) public constant returns (bytes32 data) {
        return sha3(_from, _to, _token, _value);
    }

    function max(uint a, uint b) internal constant returns (uint) {
        if (a > b) return a;
        else return b;
    }

    function min(uint a, uint b) internal constant returns (uint) {
        if (a < b) return a;
        else return b;
    }
}

pragma solidity ^0.4.17;

import '../RaidenMicroTransferChannels.sol';
import '../Token.sol';

/*
 * This is a contract used for testing RaidenMicroTransferChannels.
 */

contract Delegate {

    RaidenMicroTransferChannels public microraiden;
    Token public token;

    function setup(address _token_address, address _microraiden_contract) external {
        require(_microraiden_contract != 0x0);
        require(_token_address != 0x0);
        microraiden = RaidenMicroTransferChannels(_microraiden_contract);
        token = Token(_token_address);
    }

    function createChannelERC20(address _sender_address, address _receiver_address, uint192 _deposit) external {
        token.approve(address(microraiden), _deposit);
        microraiden.createChannelDelegate(_sender_address, _receiver_address, _deposit);
    }

    function createChannelERC223(uint192 _deposit, bytes _data) external {
        token.transfer(address(microraiden), _deposit, _data);
    }

    function topUpERC20(address _sender_address, address _receiver_address, uint32 _open_block_number, uint192 _deposit) external {
        token.approve(address(microraiden), _deposit);
        microraiden.topUpDelegate(_sender_address, _receiver_address, _open_block_number, _deposit);
    }

    function topUpERC223(uint192 _deposit, bytes _data) external {
        token.transfer(address(microraiden), _deposit, _data);
    }
}

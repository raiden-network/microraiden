# Raiden MicroTransfer Channels Contract


- _Sender_ = token sender
- _Receiver_ = token receiver
- _Contract_ = Raiden MicroTransferChannels Smart Contract
- _Token_ = RDNToken


## Opening a transfer channel

### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `createChannel`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 82963

 * `_to` = `Contract.address`
 * `_value` = deposit value (number of tokens)
 * `_data` is the equivalent of `msg.data` when calling `createChannel`
   - in web3.js, `var _data = Contract.createChannel.getData(_sender, _receiver, _deposit);` https://github.com/ethereum/wiki/wiki/JavaScript-API#web3ethcontract
   - in web3.py
   ```
    from ethereum.abi import (
      ContractTranslator
    )
    ct = ContractTranslator(abi)
    _data = ct.encode('createChannel', [sender, receiver, deposit])
   ```

![ChannelOpen_ERC223](/contracts/docs/diagrams/ChannelOpen_223.png)

### ERC20 compatible

```py
# approve token transfers to the contract from the Sender's behalf
Token.approve(contract, deposit)

Contract.createChannelERC20(receiver, deposit)
```
Gas cost (testing): 109133

![ChannelOpen_ERC20](/contracts/docs/diagrams/ChannelOpen_20.png)


## Topping up a channel

Adding tokens to an already opened channel, who's `deposit > 0`

### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `topUp`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 63872

 * `_to` = `Contract.address`
 * `_value` = deposit value (number of tokens)
 * `_data` is the equivalent of `msg.data` when calling `topUp`
   - in web3.js, `var _data = Contract.topUp.getData(_sender, _receiver, _open_block_number, _added_deposit);`
   - in web3.py
   ```
    from ethereum.abi import (
      ContractTranslator
    )
    ct = ContractTranslator(abi)
    _data = ct.encode('topUp', [_sender, _receiver, _open_block_number, _added_deposit])
   ```

 ![ChannelTopUp_223](/contracts/docs/diagrams/ChannelTopUp_223.png)


### ERC20 compatible

```py
#approve token transfers to the contract from the Sender's behalf
Token.approve(contract, added_deposit)

Contract.createChannelERC20(receiver, deposit)
```
Gas cost (testing): 90144

 ![ChannelTopUp_20](/contracts/docs/diagrams/ChannelTopUp_20.png)


## Generating and validating a transfer


Sender has to provide a **balance proof**:
- **balance message**: `receiver`, `open_block_number`, `balance`
- **signed balance message**: `balance_msg_sig`
  - `Contract.balanceMessageHash(receiver, open_block_number, balance)` -> signed by the Sender with MetaMask


Balance proof signature verification:

 - `Contract.verifyBalanceProof(receiver, open_block_number, balance, balance_msg_sig)` -> returns the Sender's address



## Generating and validating a closing agreement


Sender has to provide a **balance proof** and a **closing agreement proof**
- **balance message**: `receiver`, `open_block_number`, `balance`
- **signed balance message**: `balance_msg_sig`
- **double signed balance message**: `closing_sig` - signed by both the sender and the receiver
 - `Contract.closingAgreementMessageHash(balance_msg_sig)`
 - Receiver signs this hash with MetaMask and sends it to the Sender


Closing agreement signature verification:

- `Contract.verifyClosingSignature(balance_msg_sig, closing_sig)` -> returns the Receiver's address


## Closing a channel

```py

# 1. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 70947
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 2. Client calls Contract with receiver's closing signature = instant close & settle
# Gas cost (testing): 80764
Contract.close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

# 3. Client calls Contract without receiver's closing signature = settlement period starts
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.a. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 122888
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.b. Client calls Contract after settlement period ends
# Gas cost (testing): 114135
Contract.settle(receiver, open_block_number)

```


![ChannelCycle.png](/contracts/docs/diagrams/ChannelCycle.png)

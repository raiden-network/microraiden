# RaidenMicroTransferChannels Smart Contract

Smart Contracts, Unittests and Infrastructure for RaidenPaymentChannel Smart Contracts.


 * [Contract Addresses](#contract-addresses)
 * [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Usage](#usage)
   - [Deployment](#deployment)
   - [Generated docs](#generated-docs)
 * [API](#api)
   - [Opening a transfer channel](#opening-a-transfer-channel)
   - [Topping up a channel](#topping-up-a-channel)
   - [Generating and validating a transfer](#generating-and-validating-a-transfer)
   - [Generating and validating a closing agreement](#generating-and-validating-a-closing-agreement)
   - [Closing a channel](#closing-a-channel)


## Installation

The Smart Contracts can be installed separately from the other components of the RaidenMicroTransferChannels App.

### Prerequisites

 * Python 3.6
 * [pip](https://pip.pypa.io/en/stable/)

### Setup

 * pip install -r requirements.txt

### Usage

- from `root/contracts`:

```sh

# compilation
populus compile

# tests
py.test
py.test -p no:warnings -s
py.test tests/test_uraiden.py -p no:warnings -s

# Recommended for speed:
# you have to comment lines in tests/conftest.py to use this
pip install pytest-xdist==1.17.1
py.test -p no:warnings -s -n NUM_OF_CPUs

```

### Deployment



#### Chain setup for testing

Note - you can change RPC/IPC chain connection, timeout parameters etc. in [/contracts/populus.json](/contracts/populus.json)

 * `privtest`
   - start:
   ```
   geth --ipcpath="~/Library/Ethereum/privtest/geth.ipc" --datadir="~/Library/Ethereum/privtest"  --dev  --rpccorsdomain '*'  --rpc  --rpcport 8545 --rpcapi eth,net,web3,personal --unlock 0xf590ee24CbFB67d1ca212e21294f967130909A5a --password ~/password.txt

   # geth console
   # you have to mine yourself: miner.start()
   geth attach ipc:/Users/loredana/Library/Ethereum/privtest/geth.ipc
   ```

 * `kovan`
   - faucet: https://gitter.im/kovan-testnet/faucet
   - change default account: [/contracts/populus.json#L177](/contracts/populus.json#L177)
   - start https://github.com/paritytech/parity
   ```
   parity --geth --chain kovan --force-ui --reseal-min-period 0 --jsonrpc-cors http://localhost --jsonrpc-apis web3,eth,net,parity,traces,rpc,personal --unlock 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb --password ~/password.txt --author 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb
   ```
 * `ropsten`
   - faucet: https://www.reddit.com/r/ethdev/comments/61zdn8/if_you_need_some_ropsten_testnet_ethers/
   - change default account: [/contracts/populus.json#L49](/contracts/populus.json#L49)
   - start:
   ```
   geth --testnet --rpc  --rpcport 8545 --unlock 0xbB5AEb01acF5b75bc36eC01f5137Dd2728FbE983 --password ~/password.txt

   ```

 * `rinkeby`
   - https://www.rinkeby.io/ (has a Faucet)
   - change default account: [/contracts/populus.json#L212](/contracts/populus.json#L212)
   - start:
   ```
   # First time
   geth --datadir="~/Library/Ethereum/rinkeby" --rpc --rpcport 8545 init ~/Library/Ethereum/rinkeby.json
   geth --networkid=4 --ipcpath="~/Library/Ethereum/rinkeby/geth.ipc" --datadir="~/Library/Ethereum/rinkeby" --cache=512 --ethstats='yournode:Respect my authoritah!@stats.rinkeby.io' --bootnodes=enode://a24ac7c5484ef4ed0c5eb2d36620ba4e4aa13b8c84684e1b4aab0cebea2ae45cb4d375b77eab56516d34bfbd3c1a833fc51296ff084b770b94fb9028c4d25ccf@52.169.42.101:30303 --rpc --rpcport 8545 --unlock 0xd96b724286c592758de7cbd72c086a8a8605417f --password ~/password.txt

   # use geth console
   geth attach ipc:/Users/user/Library/Ethereum/rinkeby/geth.ipc
   ```



```sh

# Fast deploy on kovan | ropsten | rinkeby | tester | privtest

# Following two calls are equivalent
python -m deploy.deploy_testnet  # --owner is web.eth.accounts[0]
python -m deploy.deploy_testnet --chain kovan --owner 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb --challenge-period 500 --supply 10000000 --token-name CustomToken --token-decimals 18 --token-symbol TKN

# Provide a custom deployed token
python -m deploy.deploy_testnet --token-address TOKEN_ADDRESS


```


### Generated docs

[/contracts/docs/RaidenMicroTransferChannels.md](/contracts/docs/RaidenMicroTransferChannels.md)

Run `docs.sh`

Prerequisites
```
npm install -g solidity-doc

```


## API

### Opening a transfer channel

#### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `createChannel`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 86982

 * `_to` = `Contract.address`
 * `_value` = deposit value (number of tokens)
 * `_data` contains the Receiver address encoded in 20 bytes
   - in python
   ```
    _data = bytes.fromhex(receiver_address[2:].zfill(40))
   ```

![ChannelOpen_ERC223](/contracts/docs/diagrams/ChannelOpen_223.png)

#### ERC20 compatible

```py
# approve token transfers to the contract from the Sender's behalf
Token.approve(contract, deposit)

Contract.createChannelERC20(receiver, deposit)
```
Gas cost (testing): 119739

![ChannelOpen_ERC20](/contracts/docs/diagrams/ChannelOpen_20.png)


### Topping up a channel

Adding tokens to an already opened channel, who's `deposit > 0`

#### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `topUp`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 52867

 * `_to` = `Contract.address`
 * `_value` = deposit value (number of tokens)
 * `_data` contains the Receiver address encoded in 20 bytes + the open_block_number in 4 bytes
   - in python
   ```
    _data = receiver_address[2:].zfill(40) + hex(open_block_number)[2:].zfill(8)
    _data = bytes.fromhex(_data)
   ```

 ![ChannelTopUp_223](/contracts/docs/diagrams/ChannelTopUp_223.png)


#### ERC20 compatible

```py
#approve token transfers to the contract from the Sender's behalf
Token.approve(contract, added_deposit)

Contract.createChannelERC20(receiver, deposit)
```
Gas cost (testing): 85688

 ![ChannelTopUp_20](/contracts/docs/diagrams/ChannelTopUp_20.png)


### Generating and validating a balance proof

(to be updated post EIP712)

```python

# Sender has to provide a balance proof to the Receiver when making a micropayment
# The contract implements some helper functions for that

# Balance message
bytes32 balance_message_hash = keccak256(
  keccak256('address receiver', 'uint32 block_created', 'uint192 balance', 'address contract'),
  keccak256(_receiver_address, _open_block_number, _balance, address(this))
);

# balance_message_hash is signed by the Sender with MetaMask
balance_msg_sig

# Data is sent to the Receiver (receiver, open_block_number, balance, balance_msg_sig)

```


### Generating and validating a closing agreement

```python
from eth_utils import encode_hex

# Sender has to provide a balance proof to the Contract and
# a closing agreement proof from Receiver (closing_sig)
# closing_sig is created in the same way as balance_msg_sig, but it is signed by the Receiver

# Balance message
bytes32 balance_message_hash = keccak256(
  keccak256('address receiver', 'uint32 block_created', 'uint192 balance', 'address contract'),
  keccak256(_receiver_address, _open_block_number, _balance, address(this))
);

# balance_message_hash is signed by the Sender with MetaMask
balance_msg_sig

# balance_msg_sig is signed by the Receiver inside the microraiden code
closing_sig

# Send to the Contract (example of collaborative closing, transaction sent by Sender)
Contract.transact({ "from": Sender }).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

```

#### Balance proof / closing agreement signature verification:

```python

# Returns the Sender's address
sender = Contract.call().verifyBalanceProof(receiver, open_block_number, balance, balance_msg_sig)

```


### Closing a channel

```py

# 1. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 60100
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 2. Client calls Contract with receiver's closing signature = instant close & settle
# Gas cost (testing): 69438
Contract.close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

# 3. Client calls Contract without receiver's closing signature = settlement period starts
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.a. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 108000
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.b. Client calls Contract after settlement period ends
# Gas cost (testing): 103491
Contract.settle(receiver, open_block_number)

```


![ChannelCycle.png](/contracts/docs/diagrams/ChannelCycle.png)

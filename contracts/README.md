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



## Contract Addresses

### Kovan

```

ERC223Token  address is 0x04c7f744a0c751d89e99ae79a39060ec6f3c4397
RaidenMicroTransferChannels address is 0xffa52825c7997dd2be80fb91080500a52abd6d5b

```

### Ropsten Revival

```

ERC223Token  address is
RaidenMicroTransferChannels address is

```


### Rinkeby

```

ERC223Token  address is
RaidenMicroTransferChannels address is

```

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
pytest
pytest tests/test_raidenchannels.py -p no:warnings -s

```

### Deployment



#### Chain setup

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

# Following two calls are quivalent
python deploy/deploy_testnet.py
python deploy/deploy_testnet.py \
    --chain kovan \
    --owner 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb  \  # web3.eth.accounts[0]
    --challenge-period 30 \
    --supply 10000000 \
    --token-name ERC223Token \
    --token-decimals 18 \
    --token-symbol TKN \
    --senders 5 \
    --sender-addresses \ '0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38,0xd1bf222ef7289ae043b723939d86c8a91f3aac3f,0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a,0x0052D7B657553E7f47239d8c4431Fef001A7f99c'

# Provide a custom deployed token
python deploy/deploy_testnet.py --token-address address


```


### Generated docs

[/contracts/docs/RaidenMicroTransferChannels.md](/contracts/docs/RaidenMicroTransferChannels.md)

Run `docs.sh`

Prerequisites
```
npm install -g solidity-doc

```


## API


- _Sender_ = token sender
- _Receiver_ = token receiver
- _Contract_ = Raiden MicroTransferChannels Smart Contract
- _Token_ = ERC223Token

![ContractClass](/contracts/docs/diagrams/ContractClass.png)


### Opening a transfer channel

#### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `createChannel`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 73908

 * `_to` = `Contract.address`
 * `_value` = deposit value (number of tokens)
 * `_data` contains the Receiver address encoded in 20 bytes
   - in python
   ```
    _data = receiver_address[2:].zfill(40)
    _data = bytes.fromhex(_data)
   ```

![ChannelOpen_ERC223](/contracts/docs/diagrams/ChannelOpen_223.png)

#### ERC20 compatible

```py
# approve token transfers to the contract from the Sender's behalf
Token.approve(contract, deposit)

Contract.createChannelERC20(receiver, deposit)
```
Gas cost (testing): 104802

![ChannelOpen_ERC20](/contracts/docs/diagrams/ChannelOpen_20.png)


### Topping up a channel

Adding tokens to an already opened channel, who's `deposit > 0`

#### ERC223 compatible (recommended)

Sender sends tokens to the Contract, with a payload for calling `topUp`.
```
Token.transfer(_to, _value, _data)
```
Gas cost (testing): 54770

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
Gas cost (testing): 85747

 ![ChannelTopUp_20](/contracts/docs/diagrams/ChannelTopUp_20.png)


### Generating and validating a balance proof


```python

# Sender has to provide a balance proof to the Receiver when making a micropayment
# The contract implements some helper functions for that

# Balance message
# Current format: "Receiver: 0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d\nBalance: 23\nChannel ID: 5"
balance_message = Contract.call().getBalanceMessage(receiver, open_block_number, balance)

# Transform message to hexadecimal format
# For the above example, result will be: 0x19457468657265756d205369676e6564204d6573736167653a0a3738
from eth_utils import encode_hex
balance_message_hex = encode_hex(balance_message)

# balance_message_hex is signed by the Sender with MetaMask / Parity
# For the above example, result will be: 0x52656365697665723a203078646365636561663366633563306136336431393564363962316139303031316237623139363530640a42616c616e63653a2032330a4368616e6e656c2049443a2035
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
balance_message = Contract.call().getBalanceMessage(receiver, open_block_number, balance)
balance_message_hex = encode_hex(balance_message)

# balance_message_hex is signed by the Sender with MetaMask / Parity
balance_msg_sig

# balance_message_hex is signed by the Receiver with MetaMask / Parity
closing_sig

# Send to the Contract (example of collaborative closing, transaction sent by Sender)
Contract.transact({ "from": Sender }).close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

```

#### Balance proof / closing agreement signature verification:

```python

# Returns the Sender's address
sender = Contract.call().verifyBalanceProof(receiver, open_block_number, balance, balance_msg_sig)

# Returns the Receiver's address
receiver = Contract.call().verifyBalanceProof(receiver, open_block_number, balance, closing_sig)


```


### Closing a channel

```py

# 1. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 107105
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 2. Client calls Contract with receiver's closing signature = instant close & settle
# Gas cost (testing): 163375
Contract.close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)

# 3. Client calls Contract without receiver's closing signature = settlement period starts
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.a. Receiver calls Contract with the sender's signed balance message = instant close & settle
# Gas cost (testing): 199532
Contract.close(receiver, open_block_number, balance, balance_msg_sig)

# 3.b. Client calls Contract after settlement period ends
# Gas cost (testing): 149193
Contract.settle(receiver, open_block_number)

```


![ChannelCycle.png](/contracts/docs/diagrams/ChannelCycle.png)

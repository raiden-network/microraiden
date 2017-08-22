# RaidenMicroTransferChannels Smart Contract

Smart Contracts, Unittests and Infrastructure for RaidenPaymentChannel Smart Contracts.

## Current addresses

### Kovan

```

RDNToken  address is 0x6b3da80008814e116a3963065b77928be91cfa93
RaidenMicroTransferChannels address is 0x7e1528bfc6c3fd9863055bb0d4f89d69aaacdb5c

```

### Ropsten

```

RDNToken address is
RaidenMicroTransferChannels address is

```


### Rinkeby

```

RDNToken address is
RaidenMicroTransferChannels address is

```


## API

 * API logic & gas cost estimations: [/contracts/docs/logic.md](/contracts/docs/logic.md)
 * Generated docs: [/contracts/docs/RaidenMicroTransferChannels.md](/contracts/docs/RaidenMicroTransferChannels.md)


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
   - change default account: [/contracts/populus.json#L180](/contracts/populus.json#L180)
   - start https://github.com/paritytech/parity
   ```
   parity --geth --chain kovan --force-ui --reseal-min-period 0 --jsonrpc-cors http://localhost --jsonrpc-apis web3,eth,net,parity,traces,rpc,personal --unlock 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb --password ~/password.txt --author 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb
   ```
 * `ropsten`
   - change default account: [/contracts/populus.json#L52](/contracts/populus.json#L52)
   - start:
   ```
   geth --testnet --rpc  --rpcport 8545 --unlock 0xbB5AEb01acF5b75bc36eC01f5137Dd2728FbE983 --password ~/password.txt

   ```

 * `rinkeby`
   - https://www.rinkeby.io/ (has a Faucet)
   - change default account: [/contracts/populus.json#L215](/contracts/populus.json#L215)
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
python deploy/deploy_testnet.py --chain kovan --challenge-period 30 --supply 10000000 --token-name RDNToken --token-decimals 6 --token-symbol RDN --senders 5 --sender-addresses '0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38,0xd1bf222ef7289ae043b723939d86c8a91f3aac3f,0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a,0x0052D7B657553E7f47239d8c4431Fef001A7f99c'

# Provide a custom token
python deploy/deploy_testnet.py --token-address address


```


### Automatic docs creation

Run `docs.sh`

Prerequisites
```
npm install -g solidity-doc

```

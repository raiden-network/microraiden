# RaidenMicroTransferChannels Smart Contract

Smart Contracts, Unittests and Infrastructure for RaidenPaymentChannel Smart Contracts.

## Current addresses

### Kovan

RDNToken address is `0xa9a7b9864de5217a0d1431a21823360ba1c6af12`
RaidenMicroTransferChannels address is `0x794bf0bb5dcf528c4b631c699ff37e91257fac84`


### Ropsten

- not yet deployed


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

 * `kovan`
   - change default account: https://github.com/loredanacirstea/raiden-micropayment-service/blob/master/contracts/populus.json#L136
   - start https://github.com/paritytech/parity
   ```
   parity --geth --chain kovan --force-ui --reseal-min-period 0 --jsonrpc-cors http://localhost --jsonrpc-apis web3,eth,net,parity,traces,rpc,personal --unlock 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb --password ~/password.txt --author 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb
   ```


```sh

# Fast deploy on kovan / ropsten / testrpc

# Following two calls are quivalent
python deploy/deploy_testnet.py
python deploy/deploy_testnet.py --chain kovan --challenge-period 30 --supply 10000000 --token-name RDNToken --token-decimals 6 --token-symbol RDN --senders '0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38,0xd1bf222ef7289ae043b723939d86c8a91f3aac3f,0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a,0x0052D7B657553E7f47239d8c4431Fef001A7f99c'

# Provide a custom token
python deploy/deploy_testnet.py --token-address address

# Performance test
python deploy/deploy_performancetest.py

```


### Automatic docs creation

Run `docs.sh`

Prerequisites
```
npm install -g solidity-doc

```

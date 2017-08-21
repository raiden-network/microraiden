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

# deploy
python deploy/deploy_testnet.py
python deploy/deploy_performancetest.py

```

#### Deployment - chain setup

 * `kovan`
   - change default account: https://github.com/loredanacirstea/raiden-micropayment-service/blob/master/contracts/populus.json#L136
   - start https://github.com/paritytech/parity
   ```
   parity --geth --chain kovan --force-ui --reseal-min-period 0 --jsonrpc-cors http://localhost --jsonrpc-apis web3,eth,net,parity,traces,rpc,personal --unlock 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb --password ~/password.txt --author 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb
   ```


### Automatic docs creation

Run `docs.sh`

Prerequisites
```
npm install -g solidity-doc

```

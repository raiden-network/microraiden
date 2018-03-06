# µRaiden [![Build Status](https://api.travis-ci.org/raiden-network/microraiden.svg)](https://travis-ci.org/raiden-network/microraiden)

[![Join the chat at https://gitter.im/raiden-network/microraiden](https://badges.gitter.im/raiden-network/microraiden.svg)](https://gitter.im/raiden-network/microraiden?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


µRaiden is an off-chain, cheap, scalable and low-latency micropayment solution.

[µRaiden documentation](https://microraiden.readthedocs.io/)


## Smart Contract

Current version: `0.2.0` (second Bug Bounty release). Verifiable with `RaidenMicroTransferChannels.call().version()`.
Note that a new µRaiden release might include changing the Ethereum address used for the smart contract, in case we need to deploy an improved contract version.

The `RaidenMicroTransferChannels` contract has been deployed on the main net: [0x1440317CB15499083dEE3dDf49C2bD51D0d92e33](https://etherscan.io/address/0x1440317CB15499083dEE3dDf49C2bD51D0d92e33)

The following parameters were used:
- `token_address`: `0x255aa6df07540cb5d3d297f0d0d4d84cb52bc8e6`
- `challenge_period`: `8640` (blocks, rough equivalent of 36 hours)


There have been internal and external audits of the above contract. That being said, we do not recommend them to be used in production before a stable `1.0.0` release is made. All contracts are WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. Use at your own risk.

A stable release depends on the [SignTypedData - EIP712](https://github.com/ethereum/EIPs/pull/712) standard being finalized. We are aware that the current supported implementation of this standard has security issues.


### Kovan


- CustomToken address is:  [0xb5fdb634904ebe09196c506a4cc4250202f0988f](https://kovan.etherscan.io/address/0xb5fdb634904ebe09196c506a4cc4250202f0988f)
- RaidenMicroTransferChannels address is: [0xed94e711e9de1ff1e7dd34c39f0d4338a6a6ef92](https://kovan.etherscan.io/address/0xed94e711e9de1ff1e7dd34c39f0d4338a6a6ef92#code)


### Ropsten

- CustomToken address is:  [0xff24d15afb9eb080c089053be99881dd18aa1090](https://ropsten.etherscan.io/address/0xff24d15afb9eb080c089053be99881dd18aa1090)
- RaidenMicroTransferChannels address is: [0x74434527b8e6c8296506d61d0faf3d18c9e4649a](https://ropsten.etherscan.io/address/0x74434527b8e6c8296506d61d0faf3d18c9e4649a#code)


### Rinkeby

- CustomToken address is:  [0xf0f863ca785047075f6a92d28fd7dee4de47895e](https://rinkeby.etherscan.io/address/0xf0f863ca785047075f6a92d28fd7dee4de47895e)
- RaidenMicroTransferChannels address is: [0xbec8fb898e6da01152576d1a1acdd2c957e56fb1](https://rinkeby.etherscan.io/address/0xbec8fb898e6da01152576d1a1acdd2c957e56fb1#code)


## Brief Overview

µRaiden is not part of the [Raiden Network](https://github.com/raiden-network/raiden). However, it was built using the same state channel idea and implements it in a less general fashion focusing on the concrete application of micropayments for paywalled content.

The main differences between the Raiden Network and µRaiden are:
 * µRaiden is a many-to-one unidirectional state channel protocol, while the Raiden Network is a many-to-many bidirectional solution and implies a more complex design of channel networks. This allows the Raiden Network to efficiently send transfers without being forced to pay for opening new channels with people who are already in the network.
 * µRaiden off-chain transactions do not cost anything, as they are only exchanged between sender and receiver. The Raiden Network has a more complicated incentive-based off-chain transport of transaction information, from one user to another (following the channel network path used to connect the sender and the receiver).


### Tokens and Channel Manager Contract

µRaiden uses its own token for payments which is both [ERC20](https://github.com/ethereum/EIPs/issues/20) and [ERC223](https://github.com/ethereum/EIPs/issues/223) compliant.

In a nutshell, clients (subsequently called "senders") wanting to access a provider's payable resources, will [open a micropayment channel](http://microraiden.readthedocs.io/en/latest/contract/index.html#opening-a-transfer-channel) with the provider ("receiver") and fund the channel with a number of tokens. These escrowed tokens will be kept by a third party contract that manages opening and closing of channels.

### Off-chain transactions

However, the heart of the system lies in its sender -> receiver off-chain transactions. They offer a secure way to keep track of the last verified channel balance. The channel balance is calculated each time the sender pays for a resource. He is prompted to sign a so-called balance proof, i.e., a message that provably confirms the total amount of transfered tokens. This balance proof is then sent to the receiver's server. If the balance proof checks out after comparing it with the last received balance and verifying the sender's signature, the receiver replaces the old balance value with the new one.

### Closing and settling channels

A visual description of the process can be found [here](http://microraiden.readthedocs.io/en/latest/contract/index.html#closing-a-channel).

When a sender wants to close a channel, a final balance proof is prepared and sent to the receiver for a closing signature. In the happy case, the receiver signs and sends the balance proof and his signature to the smart contract managing the channels. The channel is promptly closed and the receiver debt is settled. If there are surplus tokens left, they are returned to the sender.

In the case of an uncooperative receiver (that refuses to provide his closing signature), a sender can send his balance proof to the contract and trigger a challenge period. The channel is marked as closed, but the receiver can still close and settle the debt if he wants. If the challenge period has passed and the channel has not been closed, the sender can call the contract's settle method to quickly settle the debt and remove the channel from the contract's memory.

What happens if the sender attempts to cheat and sends a balance proof with a smaller balance? The receiver server will notice the error and automatically send a request to the channel manager contract during the challenge period to close the channel with his latest stored balance proof.

There are incentives for having a collaborative channel closing. On-chain transaction gas cost is significantly smaller when the receiver sends a single transaction with the last balance proof and his signature, to settle the debt. Also, gas cost is acceptable when the sender sends the balance proof along with the receiver's closing signature. Worst case scenario is the receiver closing the channel during the challenge period. Therefore, trustworthy sender-receiver relations are stimulated.

Try out the µRaiden demo and build your own customized version, following our instructions below!


## Quick Start

 * install the Proxy component (more details [here](http://microraiden.readthedocs.io/en/latest/proxy-tutorial.html)):

```bash
virtualenv -p python3 env
. env/bin/activate
pip install microraiden
```

* install the WebUI component for the paywall examples

Note that while the `RaidenMicroTransferChannels` contract supports multiple open channels between a sender and a receiver, the WebUI component only supports one.

```
cd microraiden/microraiden/webui/microraiden
npm i && npm run build
```

* run the Proxy component:

For an overview of parameters and default options check https://github.com/raiden-network/microraiden/blob/master/microraiden/click_helpers.py

For chain and contract settings change: https://github.com/raiden-network/microraiden/blob/master/microraiden/config.py

```
cd microraiden
python -m microraiden.examples.demo_proxy --private-key <private_key_file> start
```

 * Go to the paywalled resource pages:
    - http://localhost:5000/teapot


# µRaiden

## Installation

### Using `virtualenv`

Run the following commands from the repository root directory.

```bash
virtualenv -p python3 env
. env/bin/activate
pip install -e microraiden
```

#### Using microraiden in pip's _editable_ mode
Because of `gevent` you will need to install microraiden's requirements first.
```bash
virtualenv -p python3 env
. env/bin/activate
git clone git@github.com:raiden-network/microraiden.git
cd microraiden/microraiden
pip install -r requirements-dev.txt
pip install -e .
```

### Using a global `pip3` installation

```bash
sudo pip3 install -e microraiden
```

## Execution

### HTTP Proxy
There are several examples that demonstrate how to serve custom content. To try them, run one of the following commands from the `microraiden` directory:
```bash
python3 -m microraiden.examples.demo_proxy --private-key <private_key_file> start
```
or
```bash
python3 -m microraiden.examples.wikipaydia --private-key <private_key_file> --private-key-password-file <password_file> start
```
By default, the web server listens on `0.0.0.0:5000`. The private key file should be in the JSON format produced by Geth/Parity and must be readable and writable only by the owner to be accepted (`-rw-------`). A ``--private-key-password-file`` option can be specified, containing the password for the private key in the first line of the file. If it's not provided, the password will be prompted interactively.
An Ethereum node RPC interface is expected to respond on http://localhost:8545. Alternatively, you can use [Infura infrastructure](https://infura.io/) as a RPC provider.
### M2M Client
```bash
python3 -m microraiden.examples.m2m_client --key-path <path to private key file> --key-password-path <password file>
```

## Library usage

### Client
The µRaiden client backend used by the M2M sample client can be used as a standalone library. After installation, import the following class:
```python
from microraiden import Client

client = Client('<hex-encoded private key>')
```

Alternatively you can specify a path to a JSON private key, optionally specifying a file containing the password. If it's not provided, it'll be prompted interactively.
```python
client = Client(key_path='<path to private key file>', key_password_file='<path to password file>')
```

This client object allows interaction with the blockchain and offline-signing of transactions and Raiden balance proofs.

An example lifecycle of a `Client` object could look like this:

```python
from microraiden import Client

receiver = '0xb6b79519c91edbb5a0fc95f190741ad0c4b1bb4d'
privkey = '0x55e58f57ec2177ea681ee461c6d2740060fd03109036e7e6b26dcf0d16a28169'

# 'with' statement to cleanly release the client's file lock in the end.
with Client(privkey) as client:

    channel = client.get_suitable_channel(receiver, 10)
    channel.create_transfer(3)
    channel.create_transfer(4)

    print(
        'Current balance proof:\n'
        'From: {}\n'
        'To: {}\n'
        'Channel opened at block: #{}\n'  # used to uniquely identify this channel
        'Balance: {}\n'                   # total: 7
        'Signature: {}\n'                 # valid signature for a balance of 7 on this channel
        .format(
            channel.sender, channel.receiver, channel.block, channel.balance, channel.balance_sig
        )
    )

    channel.topup(5)                      # total deposit: 15

    channel.create_transfer(5)            # total balance: 12

    channel.close()

    # Wait for settlement period to end.

    channel.settle()

    # Instead of requesting a close and waiting for the settlement period to end, you can also perform
    # a cooperative close, provided that you have a receiver-signed balance proof that matches your
    # current channel balance.

    channel.close_cooperatively(closing_sig)
```

The values required for a valid balance proof required by the receiver end are printed above. Make sure to let them know.

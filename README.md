# Raiden Micropayments Service


Raiden Micropayments Service (RMPS) is an off-chain, cheap, scalable and low-latency micropayment solution.


## Brief Overview

RMPS is not part of [Raiden](https://github.com/raiden-network/raiden). However, it was built using the same state channel idea and implements it in a less general fashion focusing on the concrete application of micropayments for paywalled content.

The main differences between Raiden and RMPS are:
 * RMPS is a many-to-one unidirectional state channel protocol, while Raiden is a many-to-many bidirectional solution and implies a more complex design of channel networks. This allows Raiden to efficiently send transfers without being forced to pay for opening new channels with people who are already in the network.
 * RMPS off-chain transactions do not cost anything at this point, as they are only exchanged between sender and receiver. Raiden has a more complicated incentive-based off-chain transport of transaction information, from one user to another (following the channel network path used to connect the sender and the receiver).


### Tokens and Channel Manager Contract

RMPS uses it's own token for payments which is both [ERC20](https://github.com/ethereum/EIPs/issues/20) and [ERC223](https://github.com/ethereum/EIPs/issues/223) compliant.

In a nutshell, clients (subsequently called "senders") wanting to access a provider's payable resources, will [open a micropayment channel](/contracts#opening-a-transfer-channel) with the provider ("receiver") and fund the channel with a number of tokens. These escrowed tokens will be kept by a third party contract that manages opening and closing of channels.

### Off-chain transactions

A visual description of the process can be found [here](/docs/dev_overview.md#off-chain-messages).

However, the heart of the system lies in its sender -> receiver off-chain transactions. They offer a secure way to keep track of the last verified channel balance. The channel balance is calculated each time the sender pays for a resource. He is prompted to sign a so called balance proof, i.e., a message that provably confirms the total amount of transfered tokens. This balance proof is then sent to the receiver's server. If the balance proof checks out after comparing it with the last received balance and verifying the sender's signature, the receiver replaces the old balance value with the new one.

### Closing and settling channels

A visual description of the process can be found [here](/contracts#closing-a-channel).

When a sender wants to close a channel, a final balance proof is prepared and sent to the receiver for a closing signature. In the happy case, the receiver signs and sends the balance proof and his signature to the smart contract managing the channels. The channel is promptly closed and the receiver debt is settled. If there are surplus tokens left, they are returned to the sender.

In the case of an uncooperative receiver (that refuses to provide his closing signature), a sender can send his balance proof to the contract and trigger a challenge period. The channel is marked as closed, but the receiver can still close and settle the debt if he wants. If the challenge period has passed and the channel has not been closed, the sender can call the contract's settle method to quickly settle the debt and remove the channel from the contract's memory.

What happens if the sender attempts to cheat and sends a balance proof with a smaller balance? The receiver server will detect the error and automatically send a request to the channel manager contract during the challenge period to close the channel with his latest stored balance proof.

There are incentives for having a collaborative channel closing. On-chain transaction gas cost is significantly smaller when the receiver sends a single transaction with the last balance proof and his signature, to settle the debt. Also, gas cost is acceptable when the sender sends the balance proof along with the receiver's closing signature. Worst case scenario is the receiver closing the channel during the challenge period. Therefore, trustworthy sender-receiver relations are stimulated.

Try out the Raiden Micropayments Service demo and build your own customized version, following our instructions below!


## Quick Start

 * install and run the Proxy component (more details [here](/raiden_mps/README.md)):

```

cd raiden-micropayment-service
virtualenv -p python3 env
. env/bin/activate
pip install -e raiden_mps
cd raiden_mps
python3 -m raiden_mps.proxy

```

 * Go to the paywalled resource pages:
    - http://localhost:5000/doggo.jpg
    - http://localhost:5000/kitten.jpg
    - http://localhost:5000/teapot.jpg
    - http://localhost:5000/test.txt


## How To

You can use the configuration for the above default example for creating your own payment channel service.

 * MicroRaiden Paywall Tutorial:
   - Proxy: [/docs/proxy-tutorial.md](/docs/proxy-tutorial.md)
   - Web Interface: [/raiden_mps/raiden_mps/webui/README.md](/raiden_mps/raiden_mps/webui/README.md)
 * Various paywall [examples](/raiden_mps/raiden_mps/examples)


## Development Documentation

 * Components Overview: [/docs/dev_overview.md](/docs/dev_overview.md)
 * MicroRaiden Service Setup: [/raiden_mps/README.md](/raiden_mps/README.md)
 * Smart Contracts Setup: [/contracts/README.md](/contracts/README.md)

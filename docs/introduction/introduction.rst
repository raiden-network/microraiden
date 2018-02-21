A quick classification
=======================

µRaiden is not part of the `Raiden
Network <https://github.com/raiden-network/raiden>`__. However, it was
built using the same state channel idea and implements it in a less
general fashion focusing on the concrete application of micropayments
for paywalled content.

The main differences between the Raiden Network and µRaiden are:

- **µRaiden** is a many-to-one unidirectional state channel protocol.
  
In comparison, the **Raiden Network** is a many-to-many bidirectional solutio and implies
a more complex design of channel networks. This allows the Raiden
Network to efficiently send transfers without being forced to pay for
opening new channels with people who are already in the network. 

- **µRaiden** off-chain transactions do not cost anything as they are only exchanged between sender and receiver

The **Raiden Network** has a more complicated incentive-based off-chain transport of transaction
information, from one user to another (following the channel network
path used to connect the sender and the receiver).



Sender / Receiver
===================

Since µRaiden enables easy micropayments from one party to another, the application is
structured in 2 logically separated parts:

- the `Sender` or `Client` side of a payment
- the `Receiver` or `Proxy-Server` side of a payment 

The `Sender` is the one who initially deposits Ether in the µRaiden payment channel.
From this point on he signs so called `balance proofs` with his private key.
A balance-proof functions as a valid micropayment, once the `Receiver` gets hold of it and keeps it on his disk.

The µRaiden application has different implementations for different scenarios for the `Sender` side:

- a JavaScript client that runs in the Senders browser whenever the Sender visits the Receivers webpage
- a Python client that runs on the Senders machine and makes http requests to the Receivers Proxy-Server instance

A typical use case for the **JavaScript** client would be a content provider, who wants to receive micropayments for accessing 
paywalled content. The content provider is the `Receiver` in this scenario and he would integrate µRaidens `Proxy-Server`
for example in his flask or Django backend.
At the same time, the content provider would serve an implementation of µRaidens JavaScript Client from his webpage.
All the consumer of the paywalled content now needs is an Ethereum account that is backed with some RDN and that is web3 accessible (
for example with MetaMask). The JavaScript client will run in the consumers browser and once it needs to sign a microtransaction the
MetaMask plugin will pop up and ask for confirmation.

The **Python client** would get mainly used in Machine-to-Machine (M2M) applications or more customized applications without the use of a browser.
In this scenario, the `Sender` has to actively install the client application and connect it to his standard blockchain-interface (like geth or parity).The client will then send out http-requests to a known `Receiver` that is running a **Proxy-Server** application.
Price information on the requested resource will be sent from the `Receiver` to the `Sender` in a custom http-Header.
Vice versa, once the `Sender` has processed his business-logic (like evaluating the price), he will repeat the http-request with a matching
`balance proof` embedded in the custom http-Header.
This balance proof signature represents the actual micropayment and should be followed up by the `Receiver` with the delivery of the requested resource.

.. figure:: /diagrams/uRaidenOverview.png
   :alt:

Off-chain transactions
~~~~~~~~~~~~~~~~~~~~~~~

A visual description of the process can be found
:doc:`here <../specifications/offchain>`.

.. TODO this is the old text - since we have a layman explanation above, we should go into more detail on signatures etc
The heart of the system lies in its sender -> receiver
off-chain transactions. They offer a secure way to keep track of the
last verified channel balance. The channel balance is calculated each
time the sender pays for a resource. He is prompted to sign a so-called
balance proof, i.e., a message that provably confirms the total amount
of transfered tokens. This balance proof is then sent to the receiver's
server. If the balance proof checks out after comparing it with the last
received balance and verifying the sender's signature, the receiver
replaces the old balance value with the new one.


Smart Contract
===============

To be exact, there is a third party involved in µRaiden:

- the `Enforcing` or `Smart Contract` part

This is the part where the trustless nature of the Ethereum blockchain comes into play.
The contract acts as the intermediary, that locks up the initial deposit from the `Sender` and enforces a possible
payout of the funds based on the signed balance proofs, that the `Sender` sent out to the `Receiver` without the use
of a blockchain.

Once the `Receiver` has a balance proof, it's easy for the `Receiver` to prove to the contract that the `Sender` owes him some tokens.
With the balance proof, the contract now can reconstruct the public key of the `Sender` and knows with certainty that the Sender
must have agreed to the updated balance.

This means that there are only 2 transactions that have to happen on the blockchain:
- the initial `opening` of the channel with the prepaid amount the sender eventually wants to spent during the channels lifetime
- the final `closing` of the channel, where the senders initial deposit is paid out to the receiver and sender, based on the agreed on off chain balances 

If the channel runs low on funds before it is closed, the sender can increase the transferable amount of the channel
with a `topup` transaction on-chain.

After a channel is closed, it can't be used anymore. If the business-relationship between the same sender and receiver should revive again,
a new channel has to be opened.

µRaiden uses its own token for payments which is both
`ERC20 <https://github.com/ethereum/EIPs/issues/20>`__ and
`ERC223 <https://github.com/ethereum/EIPs/issues/223>`__ compliant.

Closing and settling channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A visual description of the process can be found :ref:`here <contract-closing-a-channel>`.

.. TODO again, this is the old text with some overlap to above - go a little bit more into detail how the contract recovers the pubkey etc
When a sender wants to close a channel, a final balance proof is
prepared and sent to the receiver for a closing signature. In the happy
case, the receiver signs and sends the balance proof and his signature
to the smart contract managing the channels. The channel is promptly
closed and the receiver debt is settled. If there are surplus tokens
left, they are returned to the sender.

In the case of an uncooperative receiver (that refuses to provide his
closing signature), a sender can send his balance proof to the contract
and trigger a challenge period. The channel is marked as closed, but the
receiver can still close and settle the debt if he wants. If the
challenge period has passed and the channel has not been closed, the
sender can call the contract's settle method to quickly settle the debt
and remove the channel from the contract's memory.

What happens if the sender attempts to cheat and sends a balance proof
with a smaller balance? The receiver server will notice the error and
automatically send a request to the channel manager contract during the
challenge period to close the channel with his latest stored balance
proof.

There are incentives for having a collaborative channel closing.
On-chain transaction gas cost is significantly smaller when the receiver
sends a single transaction with the last balance proof and his
signature, to settle the debt. Also, gas cost is acceptable when the
sender sends the balance proof along with the receiver's closing
signature. Worst case scenario is the receiver closing the channel
during the challenge period. Therefore, trustworthy sender-receiver
relations are stimulated.

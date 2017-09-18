# µRaiden

µRaiden components overview.

 * [HTTP Request and Response Headers](#http-request-and-response-headers)
 * [Exceptions](#exceptions)
 * [Off-Chain Messages](#off-chain-messages)
 * [Proxy](#proxy)
 * [Python Client](#python-client)
 * [Web Client](#web-client)
 * [Smart Contract](#smart-contract)

## HTTP Request and Response Headers

Encoding:
 * `address`	`0x` prefixed hex encoded
 * `uint`	`[0-9]`
 * `bytes`	`0x` prefixed hex encoded


### Response Headers


#### 200 OK


|        Headers        |   Type   |   Description                              |
| --------------------- | -------- | ------------------------------------------ |
|  RDN-Gateway-Path     | bytes    |  Path root of the channel management app   |
|  RDN-Cost             | uint     |  Cost of the payment                       |
|  RDN-Contract-Address | address  |  Address of MicroTransferChannels contract |
|  RDN-Receiver-Address | address  |  Address of the Merchant                   |
|  RDN-Sender-Address   | address  |  Address of the Client                     |
|  RDN-Sender-Balance   | uint     |  Balance of the Channel                    |



#### 402 Payment Required



|        Headers        |   Type   |   Description                              |
| --------------------- | -------- | ------------------------------------------ |
|  RDN-Gateway-Path     | bytes    |  Path root of the channel management app   |
|  RDN-Price            | uint     |  The price of answering the request        |
|  RDN-Contract-Address | address  |  Address of MicroTransferChannels contract |
|  RDN-Receiver-Address | address  |  Address of the Merchant                   |



#### 402 Payment Required (non accepted RDN-Balance-Signature )




|        Headers                  |   Type   |   Description                              |
| ---------------------           | -------- | ------------------------------------------ |
| RDN-Gateway-Path                | bytes    |  Path root of the channel management app   |
| RDN-Price                       | uint     |  The price of answering the request        |
| RDN-Contract-Address            | address  |  Address of MicroTransferChannels contract |
| RDN-Receiver-Address            | address  |  Address of the Merchant                   |
| RDN-Sender-Address              | address  |  Address of the Client                     |
| RDN-Sender-Balance              | uint     |  Balance of the Channel                    |
| RDN-Insufficient-Funds          | uint     |  Failure - either Payment value too low or balance exceeds deposit|
| RDN-Insufficient-Confirmations  | uint     |  Failure - not enough confirmations after the channel creation. Client should wait and retry. |



#### 4xx / 5xx Errors

Refund.


### Request Headers



|        Headers        |   Type   |   Description                              |
| --------------------- | -------- | ------------------------------------------ |
| RDN-Contract-Address  | address  |  Address of MicroTransferChannels contract |
| RDN-Receiver-Address  | address  |  Address of the Merchant                   |
| RDN-Sender-Address    | address  |  Address of the Client                     |
| RDN-Payment           | uint     |  Amount of the payment                     |
| RDN-Sender-Balance    | uint     |  Balance of the Channel                    |
| RDN-Balance-Signature | bytes    |  Signature from the Sender, signing the balance (post payment) |
| RDN-Open-Block        | uint     |  Opening block number of the channel required for unique identification |



## Exceptions

```

InvalidBalanceAmount
InvalidBalanceProof
NoOpenChannel
InsufficientConfirmations
NoBalanceProofReceived
StateContractAddrMismatch
StateReceiverAddrMismatch

```

## Off-Chain Messages

### Micropayment Sequence

(not-so-standard sequence diagram)
For a better overview, also check out how the smart contract does a transfer validation:  [/contracts/README.md#generating-and-validating-a-transfer](/contracts/README.md#generating-and-validating-a-transfer)

![](/docs/diagrams/OffChainSequence.png)

### Channel Closing Sequence

For a better overview, also check out how the smart contract does a closing signature validation:  [/contracts/README.md#generating-and-validating-a-closing-agreement](/contracts/README.md#generating-and-validating-a-closing-agreement)

![](/docs/diagrams/OffChainSequenceClosing.png)


## Proxy


### Channel manager

![](/docs/diagrams/ChannelManagerClass.png)

### Paywalled Proxy

![](/docs/diagrams/PaywalledProxyClass.png)


## Python Client

![](/docs/diagrams/PythonClientClass.png)


## Web Client

![](/docs/diagrams/JSClientClass.png)


## Smart Contract

[/contracts/README.md](/contracts/README.md)

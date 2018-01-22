# RaidenMicroTransferChannels

## Non-Constant Functions

### topUp
Increase the channel deposit with `_added_deposit`.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_added_deposit|uint192||The added token deposit with which the current deposit is increased.|

### cooperativeClose
Function called by the sender, receiver or a delegate, with all the needed signatures to close the channel and settle immediately.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_balance|uint192||The amount of tokens owed by the sender to the receiver.|
|_balance_msg_sig|bytes||The balance message signed by the sender.|
|_closing_sig|bytes||The receiver's signed balance message, containing the sender's address.|

### removeTrustedContracts
Function for removing trusted contracts. Can only be called by owner_address.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_trusted_contracts|address[]||Array of contract addresses to be removed from the trusted_contracts mapping.|

### uncooperativeClose
Sender requests the closing of the channel and starts the challenge period. This can only happen once.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_balance|uint192||The amount of tokens owed by the sender to the receiver.|

### settle
Function called by the sender after the challenge period has ended, in order to settle and delete the channel, in case the receiver has not closed the channel himself.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|

### topUpDelegate
Function that allows a delegate contract to increase the channel deposit with `_added_deposit`. Can only be called by a trusted contract. Compatibility with ERC20 tokens.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The sender's address in behalf of whom the delegate sends tokens.|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_added_deposit|uint192||The added token deposit with which the current deposit is increased.|

### addTrustedContracts
Function for adding trusted contracts. Can only be called by owner_address.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_trusted_contracts|address[]||Array of contract addresses that can be trusted to open and top up channels on behalf of a sender.|

### withdraw
Allows channel receiver to withdraw tokens.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_balance|uint192||Partial or total amount of tokens owed by the sender to the receiver. Has to be smaller or equal to the channel deposit. Has to match the balance value from `_balance_msg_sig` - the balance message signed by the sender. Has to be smaller or equal to the channel deposit.|
|_balance_msg_sig|bytes||The balance message signed by the sender.|

### createChannel
Creates a new channel between `msg.sender` and `_receiver_address` and transfers the `_deposit` token deposit to this contract. Compatibility with ERC20 tokens.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_deposit|uint192||The amount of tokens that the sender escrows.|

### tokenFallback
Opens a new channel or tops up an existing one, compatibility with ERC 223.
Can only be called from the trusted Token contract.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The address that sent the tokens to this contract.|
|_deposit|uint256||The amount of tokens that the sender escrows.|
|_data|bytes||Data needed for either creating a channel or topping it up. It always contains the sender and receiver addresses +/- a block number.|

### createChannelDelegate
Function that allows a delegate contract to create a new channel between `_sender_address` and `_receiver_address` and transfers the token deposit to this contract. Can only be called by a trusted contract. Compatibility with ERC20 tokens.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The sender's address in behalf of whom the delegate sends tokens.|
|_receiver_address|address||The address that receives tokens.|
|_deposit|uint192||The amount of tokens that the sender escrows.|

## Constant Functions

### challenge_period

#### Output

|name|type|
|---|---|
||uint32||

### getChannelInfo
Function for retrieving information about a channel.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The address that sends tokens.|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|

#### Output

Function returns: Channel information: unique_identifier, deposit, settle_block_number, closing_balance, withdrawn balance).

|name|type|
|---|---|
||bytes32||
||uint192||
||uint32||
||uint192||
||uint192||

### extractBalanceProofSignature
Returns the sender address extracted from the balance proof. dev Works with eth_signTypedData https://github.com/ethereum/EIPs/pull/712.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_balance|uint192||The amount of tokens owed by the sender to the receiver.|
|_balance_msg_sig|bytes||The balance message signed by the sender.|

#### Output

Function returns: Address of the balance proof signer.

|name|type|
|---|---|
||address||

### extractClosingSignature
Returns the receiver address extracted from the closing signature. Works with eth_signTypedData https://github.com/ethereum/EIPs/pull/712.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The address that sends tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|
|_balance|uint192||The amount of tokens owed by the sender to the receiver.|
|_closing_sig|bytes||The receiver's signed balance message, containing the sender's address.|

#### Output

Function returns: Address of the closing signature signer.

|name|type|
|---|---|
||address||

### withdrawn_balances

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
||bytes32|||

#### Output

|name|type|
|---|---|
||uint192||

### version

#### Output

|name|type|
|---|---|
||string||

### channel_deposit_bugbounty_limit

#### Output

|name|type|
|---|---|
||uint256||

### closing_requests

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
||bytes32|||

#### Output

|name|type|
|---|---|
|closing_balance|uint192||
|settle_block_number|uint32||

### channels

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
||bytes32|||

#### Output

|name|type|
|---|---|
|deposit|uint192||
|open_block_number|uint32||

### getKey
Returns the unique channel identifier used in the contract.

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
|_sender_address|address||The address that sends tokens.|
|_receiver_address|address||The address that receives tokens.|
|_open_block_number|uint32||The block number at which a channel between the sender and receiver was created.|

#### Output

Function returns: Unique channel identifier.

|name|type|
|---|---|
|data|bytes32||

### owner_address

#### Output

|name|type|
|---|---|
||address||

### trusted_contracts

#### Input parameters

|name|type|indexed|description|
|---|---|---|---|
||address|||

#### Output

|name|type|
|---|---|
||bool||

### token

#### Output

|name|type|
|---|---|
||address||




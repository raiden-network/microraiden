












# RaidenMicroTransferChannels

### RaidenMicroTransferChannels



## Functions



### Constant functions

#### balanceMessageHash




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||
|2|_balance|uint192|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|data|bytes32|||


#### challenge_period




##### Inputs

empty list


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|return0|uint8||challenge_period|


#### closingAgreementMessageHash




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_balance_msg_sig|bytes|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|data|bytes32|||


#### getChannelInfo




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|param0|bytes32|||
|1|param1|uint192|||
|2|param2|uint32|||
|3|param3|uint192|||


#### getKey




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|data|bytes32|||


#### owner

Data structures


##### Inputs

empty list


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|return0|address||Data structures|


#### token_address




##### Inputs

empty list


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|return0|address||token_address|


#### verifyBalanceProof




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||
|2|_balance|uint192|||
|3|_balance_msg_sig|bytes|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|param0|address|||


#### verifyClosingSignature




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_balance_msg_sig|bytes|||
|1|_closing_sig|bytes|||


##### Returns

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|param0|address|||






### State changing functions

#### close




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||
|2|_balance|uint192|||
|3|_balance_msg_sig|bytes|||
|4|_closing_sig|bytes|||


#### createChannel




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_deposit|uint192|||


#### createChannelERC20




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_deposit|uint192|||


#### initChallengePeriod




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||
|2|_balance|uint192|||


#### settle




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||


#### settleChannel




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||
|3|_balance|uint192|||


#### tokenFallback




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_deposit|uint256|||
|2|_data|bytes|||


#### topUp




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||
|3|_added_deposit|uint192|||


#### topUpERC20




##### Inputs

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_receiver|address|||
|1|_open_block_number|uint32|||
|2|_added_deposit|uint192|||






### Events

#### ChannelCreated

Events


##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_deposit|uint192|||


#### ChannelToppedUp




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||
|3|_added_deposit|uint192|||
|4|_deposit|uint192|||


#### ChannelCloseRequested




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||
|3|_balance|uint192|||


#### ChannelSettled




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_open_block_number|uint32|||
|3|_balance|uint192|||


#### TokenFallback




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_sender|address|||
|1|_receiver|address|||
|2|_deposit|uint192|||
|3|_data|bytes|||


#### GasCost




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|_function_name|string|||
|1|_gaslimit|uint|||
|2|_gas|uint|||





### Enums




### Structs

#### Channel




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|deposit|uint192|||
|1|open_block_number|uint32|||


#### ClosingRequest




##### Params

|#  |Param|Type|TypeHint|Description|
|---|-----|----|--------|-----------|
|0|settle_block_number|uint32|||
|1|closing_balance|uint192|||




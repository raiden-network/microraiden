[microraiden](../README.md) > [MicroChannelInfo](../interfaces/microchannelinfo.md)



# Interface: MicroChannelInfo


[MicroRaiden.getChannelInfo](../classes/microraiden.md#getchannelinfo) result


## Properties
<a id="block"></a>

###  block

**●  block**:  *`number`* 

*Defined in [index.ts:66](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L66)*



Block of current state (opened=open block number, closed=channel close requested block number, settled=settlement block number)




___

<a id="deposit"></a>

###  deposit

**●  deposit**:  *`BigNumber`* 

*Defined in [index.ts:70](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L70)*



Current channel deposited sum




___

<a id="state"></a>

###  state

**●  state**:  *`string`* 

*Defined in [index.ts:61](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L61)*



Current channel state, one of 'opened', 'closed' or 'settled'




___

<a id="withdrawn"></a>

###  withdrawn

**●  withdrawn**:  *`BigNumber`* 

*Defined in [index.ts:74](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L74)*



Value already taken from the channel




___



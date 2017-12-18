[microraiden](../README.md) > [MicroChannel](../interfaces/microchannel.md)



# Interface: MicroChannel


[MicroRaiden.channel](../classes/microraiden.md#channel) state data blueprint


## Properties
<a id="account"></a>

###  account

**●  account**:  *`string`* 

*Defined in [index.ts:31](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L31)*



Sender/client's account address




___

<a id="block"></a>

###  block

**●  block**:  *`number`* 

*Defined in [index.ts:39](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L39)*



Open channel block number




___

<a id="close_sign"></a>

### «Optional» close_sign

**●  close_sign**:  *`string`* 

*Defined in [index.ts:51](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L51)*



Cooperative close signature from receiver




___

<a id="next_proof"></a>

### «Optional» next_proof

**●  next_proof**:  *[MicroProof](microproof.md)* 

*Defined in [index.ts:47](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L47)*



Next balance proof, persisted with [MicroRaiden.confirmPayment](../classes/microraiden.md#confirmpayment)




___

<a id="proof"></a>

###  proof

**●  proof**:  *[MicroProof](microproof.md)* 

*Defined in [index.ts:43](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L43)*



Current balance proof




___

<a id="receiver"></a>

###  receiver

**●  receiver**:  *`string`* 

*Defined in [index.ts:35](https://github.com/raiden-network/microraiden/blob/99a659d/microraiden/microraiden/webui/microraiden/src/index.ts#L35)*



Receiver/server's account address




___



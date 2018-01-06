


#  microraiden

## Index

### Classes

* [Deferred](classes/deferred.md)
* [MicroRaiden](classes/microraiden.md)


### Interfaces

* [MicroChannel](interfaces/microchannel.md)
* [MicroChannelInfo](interfaces/microchannelinfo.md)
* [MicroProof](interfaces/microproof.md)
* [MicroTokenInfo](interfaces/microtokeninfo.md)
* [MsgParam](interfaces/msgparam.md)


### Variables

* [localStorage](#localstorage)


### Functions

* [asyncSleep](#asyncsleep)
* [encodeHex](#encodehex)
* [promisify](#promisify)



---
# Variables
<a id="localstorage"></a>

###  localStorage

**●  localStorage**:  *`any`* 

*Defined in [index.ts:5](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L5)*





___


# Functions
<a id="asyncsleep"></a>

###  asyncSleep

► **asyncSleep**(timeout: *`number`*): `Promise`.<`void`>



*Defined in [index.ts:133](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L133)*



Async sleep: returns a promise which will resolve after timeout


**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| timeout | `number`   |  Timeout before promise is resolved, in milliseconds |





**Returns:** `Promise`.<`void`>
Promise which will be resolved after timeout






___

<a id="encodehex"></a>

###  encodeHex

► **encodeHex**(val: *`string`⎮`number`⎮`BigNumber`*, zPadLength?: *`number`*): `string`



*Defined in [index.ts:146](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L146)*



Encode strings and numbers as hex, left-padded, if required.

0x prefix not added,


**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| val | `string`⎮`number`⎮`BigNumber`   |  Value to be hex-encoded |
| zPadLength | `number`   |  Left-pad with zeroes to this number of characters |





**Returns:** `string`
hex-encoded value






___

<a id="promisify"></a>

###  promisify

► **promisify**T(obj: *`any`*, method: *`string`*): `function`



*Defined in [index.ts:109](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L109)*



Convert a callback-based func to return a promise

It'll return a function which, when called, will pass all received parameters to the wrapped method, and return a promise which will be resolved which callback data passed as last parameter


**Type parameters:**

#### T 
**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| obj | `any`   |  A object containing the method to be called |
| method | `string`   |  A method name of obj to be promisified |





**Returns:** `function`
A method wrapper which returns a promise






___



[microraiden](../README.md) > [Deferred](../classes/deferred.md)



# Class: Deferred


Promise-based deferred class

## Type parameters
#### T 
## Index

### Properties

* [promise](deferred.md#promise)
* [reject](deferred.md#reject)
* [resolve](deferred.md#resolve)



---
## Properties
<a id="promise"></a>

###  promise

**●  promise**:  *`Promise`.<`T`>*  =  new Promise<T>((resolve, reject) => {
    this.resolve = resolve;
    this.reject = reject;
  })

*Defined in [index.ts:118](https://github.com/raiden-network/microraiden/blob/767bd8f/microraiden/microraiden/webui/microraiden/src/index.ts#L118)*





___

<a id="reject"></a>

###  reject

**●  reject**:  *`function`* 

*Defined in [index.ts:117](https://github.com/raiden-network/microraiden/blob/767bd8f/microraiden/microraiden/webui/microraiden/src/index.ts#L117)*


#### Type declaration
►(err: *`Error`*): `void`



**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| err | `Error`   |  - |





**Returns:** `void`






___

<a id="resolve"></a>

###  resolve

**●  resolve**:  *`function`* 

*Defined in [index.ts:116](https://github.com/raiden-network/microraiden/blob/767bd8f/microraiden/microraiden/webui/microraiden/src/index.ts#L116)*


#### Type declaration
►(res: *`T`*): `void`



**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| res | `T`   |  - |





**Returns:** `void`






___



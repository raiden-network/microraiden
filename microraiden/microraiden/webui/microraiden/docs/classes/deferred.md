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

*Defined in [index.ts:147](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L147)*





___

<a id="reject"></a>

###  reject

**●  reject**:  *`function`* 

*Defined in [index.ts:146](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L146)*


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

*Defined in [index.ts:145](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L145)*


#### Type declaration
►(res: *`T`*): `void`



**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| res | `T`   |  - |





**Returns:** `void`






___



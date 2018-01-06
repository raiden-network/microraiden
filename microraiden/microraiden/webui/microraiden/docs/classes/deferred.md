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

*Defined in [index.ts:121](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L121)*





___

<a id="reject"></a>

###  reject

**●  reject**:  *`function`* 

*Defined in [index.ts:120](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L120)*


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

*Defined in [index.ts:119](https://github.com/andrevmatos/microraiden/blob/0546d77/microraiden/microraiden/webui/microraiden/src/index.ts#L119)*


#### Type declaration
►(res: *`T`*): `void`



**Parameters:**

| Param | Type | Description |
| ------ | ------ | ------ |
| res | `T`   |  - |





**Returns:** `void`






___



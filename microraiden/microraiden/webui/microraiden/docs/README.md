
# MicroRaiden TypeScript/JavaScript client library

This package contains the µRaiden client javascript/typescript library.

µRaiden (read microraiden) is a payment channel framework for the Ethereum blockchain developed by [brainbot labs est](https://brainbot.li/). Its main goal is to provide a fast, cheap, open-source, many-to-one (client-server) off-chain payments framework capable of instantly transfering ERC20/ERC223-compliant tokens between a sender/client and a receiver/server, from locked deposits in on-chain channels.

## Overview

This package contains only the javascript/typescript client implementation for µRaiden.
For the server implementation, see respective [documentation](https://github.com/raiden-network/microraiden/blob/master/README.md).

As a library, it can be used in Node and browser environments.
TypeScript, ES5 CommonJS, ES5 UMD and ES6 modules transpilations are provided.
[A paywall webapp](../index.html) is available as well, to demonstrate browser usage.

The library itself does not communicate with the µRaiden server, but only with the blockchain through the web3 provider (MetaMask, Parity, Mist, etc). It's responsibility of the application using it to fill the data returned by it in the preferred protocol (out of the box, HTTP headers for Node/m2m clients, Cookies for browser environments). Again, refer to the paywall app for example of this usage.

Most of the [MicroRaiden](./docs/classes/microraiden.md) APIs return `Promise`s, which are resolved only if the operation was successful (including transaction mining, when relevant), and rejected otherwise. This makes the library compatible with the **await/async** pattern.

## Tests

You can run the tests with:

>     npm test


## API Documentation

The API documentation can be found [here](./docs/README.md). Below is a brief explaination of the main workflow for library usage. More details can be found in the [paywall demo implementation](../js/main.js).

## Workflow

1. Preparation

    1. Import:
        - `<script>` tag can be used directly in the webpage headers with the UMD implementation.
        - `const MicroRaiden = require('microraiden').MicroRaiden;` for Node
        - `import { MicroRaiden } from 'microraiden'` for TypeScript/ES6

        You need also to include/import the `web3 < 1.0` library by yourself. The other libraries are bundled with the MicroRaiden or available on `npm install`.

    2. Instantiation:

        You should load contract and token information (address, ABI) from the server. Usually, these info come in Cookies and HTTP headers, and through the `/api/1/stats` endpoint.

        With it, and after ensuring your web3 instance is injected/instantiated (Metamask can take a couple seconds to inject it, you may want to poll/wait for it to be available), you can instantiate main MicroRaiden object as:

        >     const uraiden = new MicroRaiden(web3, contractAddr, contractABI, tokenAddr, tokenABI);

2. Channel setup:

    The main state information stored in this object is the `channel` property. The MicroRaiden library implements a default storage of it through the `localStorage` feature available in browsers. [node-localstorage](https://www.npmjs.com/package/node-localstorage) can be used to make it available also in Node environments, but you can always handle it by yourself. You can also use [MicroRaiden.loadFromBlockchain](./docs/classes/microraiden.md#loadchannelfromblockchain) to load a zero-balance channel with the first open channel found for the current address and given receiver (if any). Zero-balance channels are useful to trigger server to send you its latest registered balance proof for you, allowing you to initialize the channel state without storing client-side data.

    On first usage from a client, a channel needs to be created (on chain) and tokens locked on it, to allow off-chain payments from there on. This can be done through the [MicroRaiden.openChannel](./docs/classes/microraiden.md#openchannel) method.

3. Paying:

    When making a request to a server's protected/expensive resource, you should receive a `402 PAYMENT REQUIRED` response, with a few information describing the current balance for your channel (from server's perspective, if available) and the payment required to allow access to it.

    After a channel is available (through loading of existing channel or creation of a new), you may proceed to signing the balance proofs and re-sending the request with it to the server. It should be mainly done through the [MicroRaiden.incrementBalanceAndSign](./docs/classes/microraiden.md#incrementbalanceandsign), passing the price of the resource (usually available through `RDN-Price` header or cookie), which will then be incremented on previous balance and signed by the user. The promise returned by this call should be resolved with a [MicroProof](./docs/interfaces/microproof.md) object, containing the new balance and its signature. You should then fill relevant headers/cookies, and retry the request with balance proof in it, which should make the server return a successful result.

4. Finishing:

    You should also provide ways for your user to [top up](./docs/classes/microraiden.md#topupchannel), (cooperatively, when possible, or uncooperatively, if needed) [close](./docs/classes/microraiden.md#closechannel) and [settle](./docs/classes/microraiden.md#settlechannel) their channels. Forgotten channels may lock user's tokens indefinitely, or at least until receiver's decide to close them, so provide ways for your users to view and handle them.

## Issues

You can report any issues or ask questions through the [our GitHub](https://github.com/raiden-network/microraiden/issues).

## License

Licensed under the [MIT License](./LICENSE)



## Index

### Classes

* [Deferred](classes/deferred.md)
* [MicroRaiden](classes/microraiden.md)


### Interfaces

* [ChannelCloseRequestedArgs](interfaces/channelcloserequestedargs.md)
* [ChannelCreatedArgs](interfaces/channelcreatedargs.md)
* [ChannelSettledArgs](interfaces/channelsettledargs.md)
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

*Defined in [index.ts:5](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L5)*





___


# Functions
<a id="asyncsleep"></a>

###  asyncSleep

► **asyncSleep**(timeout: *`number`*): `Promise`.<`void`>



*Defined in [index.ts:159](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L159)*



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



*Defined in [index.ts:172](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L172)*



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



*Defined in [index.ts:135](https://github.com/raiden-network/microraiden/blob/534ae10/microraiden/microraiden/webui/microraiden/src/index.ts#L135)*



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



# MicroRaiden Microtransfers Client Web Interface / Paywall page

This webpage ([index.html](./index.html)) and its associated [JS files](./js) are a small [jQuery](https://jquery.com)-based demonstration page of the [javascript client library for Raiden Microtransfers Service](./js/microraiden.js) DApp. It implements a basic paywall example, where, once the user tries to access a protected resource/URL, it'll ask for a small token transfer before allowing access to the resource, through the creation of a channel with the server address as receiver, a basic deposit, and small signed token transfers.

The library itself is compatible with current browsers and [Node.js](https://nodejs.org) environments, making use of some ES6 features (e.g. classes, arrow-functions, const and let variables, spread operator), which should be supported in most recent browsers and up-to-date Node (8+) versions.


## Browser library import

Include it below your `web3 < 1.0.0` distribution:
```
<script type="text/javascript" src="/js/web3.js"></script>
<script type="text/javascript" src="/js/microraiden.js"></script>
```


## Node library import

Just require it:
```
var MicroRaiden = require("microraiden").MicroRaiden;
```


## Instantiation

The MicroRaiden object takes as parameters a web3 instance or web3 HTTP RPC URL string as first parameter, followed by address and ABI of channel manager contract and token.
For the web3 object, if you are using injected Metamask or Parity, you may want to wait a little until it actually gets injected in the page before instantiating the client, as it may take up to a couple of seconds. It'll only use the `web3.currentProvider` of the object, and using shipped Web3 library, so it can stay compatible with [recent](https://github.com/ethereum/mist/releases/tag/v0.9.0) Mist changes.

Example:
```
var uraiden = new MicroRaiden(web3, contractAddr, contractABI, tokenAddr, tokenABI);
```


## Usage

The MicroRaiden class presents an interface mostly constituted of a Node-style callback async API, where the last parameter of almost every method is a callback in the form:
```
function callback(error, response) {...}
```

It also calls asynchronously the web3 methods, keeping it compatible with Metamask async-only interface.

The most important and relevant class attribute is the `channel` member, which stores the current channel information as:
```
{
    "account": "0x...", // User account for this channel
    "receiver" "0x...", // Receiver account for this channel
    "block": 1500123,   // Block number where channel was opened
    "balance": 0        // Current channel spent balance
}
```

This object is automatically populated on `openChannel`, and can also be loaded from `localStorage` with the `loadStoredChannel(account, receiver)` method, or provide one yourself after instance creation. Forgetting it will drive the user unable to close the channel by itself, becoming dependent on the receiver will for closing the channel.


### Basic workflow

The basic workflow for the client should be something like:

1. Load parameters and instantiate MicroRaiden object
2. Load default account using `getAccounts(callback)`
3. Get an open channel:
  1. Try to load from storage with `loadStoredChannel(account, receiver)`
  2. If no stored channels, ask for the user to make an initial deposit and open a channel, with `openChannel(account, receiver, deposit, callback)`
4. Ask the user to sign a balance proof with current balance, plus the required amount (usually, got from proxy RDN-* cookies), through `incrementBalanceAndSign(amount, callback)`
5. Require again the resource, sending along the new balance proof (usually, through RDN-* cookies)
6. If desired, give users the option to `close` and `settle` the channel


## Customization

Some options may require proxy parameters tweaking, like receiving, channel manager contract and token addresses, and required amount by resource.
The included [index.html](./index.html) page, along with client [main.js](./js/main.js) file, are a basic demonstration of above workflow/usage pattern, and can be customized or rewritten easily using only the provided library.

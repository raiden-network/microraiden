# Changelog

## Development

## 0.2.0 - 2018-01-23 - Bug Bounty Release 2

* Update contract, pypi & nmp version, update documentation. #334
* Add withdraw tokens script for allowing the receiver to withdraw tokens without closing the channel. #398
* Update documentation, switch to .rst. #345
* Fix paywall url webui injection. #396
* Smart contract - add underflow check in `settleChannel`. #394
* Update eth ticker example. #393
* Update docstrings. #386
* Fixed an issue caused by the contract version check including the maintenance number. #368
* `setup.py` now also performs npm compilation. #366
* README.md and diagrams were updated. #364
* Block syncing is now performed from a hard-coded block number instead of the genesis block. #362
* Fixed the creation of a channel manager without a contract address via click helpers. #361
* Added more documentation and updated metadata in the µRaiden web client. #360
* Fixed author and email information in pypi metadata. #359
* Some tests are automatically skipped on Travis CI. #358
* Added this changelog. #356
* Added support for `make npm`. #352
* Added support for checksummed addresses in the contract deploy script. #351
* Python tests can now be run on any real Ethereum network, e.g. Ropsten. #347
* Added support for checksummed addresses in the echo server example. #346
* Updated outdates usage of `web3`'s `RPCProvider. #343
* Updated documentation of a µRaiden quickstart in README.md. #342
* Fixed an outdated usage of `web3.currentProvider`. #341
* Added server logging messages to failed payment attempts. #340
* Added JS/TS library tests to travis execution.
* Fixed an outdated dependency issue concerning `eth-tester`. #336
* Added a hint on how to install µRaiden using `pip install -e`. #335
* Implemented contract refactoring in Python client code. #332
* Updated `populus` and `web3` libraries to newer versions. #327
* Significantly improved test coverage of JS/TS client libraries. #326
* Contract refactoring. #325
* Added functionality to allow receivers to withdraw tokens from a channel without closing it. #324
* Added functionality to allow trusted delegate contracts to open and top up channels on behalf of the sender. #322
* Fixed the badly maintained echo example and added a new test to make sure it remains functional. #318
* Adopted contract refactoring, including new closing messages, in Python code. #317
* Implemented new, safer contract closing signature in JS/TS client. #315
* Added utility functions for hierarchical popping of function `kwargs` used in passing arguments through to `requests.Session`. #312
* Improved code quality, coverage, and speed of contract tests. #310
* Moved the demo from Kovan to Ropsten, aligned the Docker build with the main demos, purged a lot of static files, and fixed an issue where a proxy would not allow multiple resources of the same class. #308
* Fixed an issue where proxy resource headers would be overridden by default headers. #305
* Added channel state recovery and contract verification to the web UI client. #301
* Error responses in a `Session` object are now returned by the request call. #300
* Updated demos to use the new paywalled flask resources API. #298
* Made µRaiden available on pypi. Enjoy your `pip install microraiden`! #296
* Merged `HTTPClient` and `DefaultHTTPClient` into a `requests`-like `Session` class. This class directly inherits `requests.Session` and can easily be used in its stead to create µRaiden-enabled client applications. Global `microraiden.requests` methods create temporary `Session` objects. #295
* The HTTP client now handles the denial of a proper closure signature by noncooperatively closing the channel on a balance of 0. The server is then expected to dispute this balance on-chain. #293
* Fixed an issue where the HTTP client would not handle nonexisting channel error messages correctly. #292
* Changed the proxy's default content type to JSON. #290, #291
* Added a lot of documentation to the µRaiden JS/TS client library. #288
* Fixed a minor issue involving a broken web UI proxy call. #287
* Added proper support for dynamic price arguments in paywalled resources. #286
* The ETH ticker test now uses mocked API values to further speed up the test. #285
* Fixed an issue that caused example tests to run very slowly. #284
* Fixed an issue where a proxy resource was not immediately returned if its price was 0. #282
* Added a `key` property to the channel class, calculating the channel's key used within the contract. #279
* Fixed a theoretical overflow vulnerability concerning the contract's challenge period. #277
* Major refactoring of `contract_proxy.py` methods. #275

    The `ContractProxy` class was replaced by stateless utility functions exposed in `microraiden.utils`. All required context objects have to be passed on each call.

* Included `ethereum-utils` in the `requirements.txt`. #274
* Contract closing signatures incorporate feedback from an internal audit, following cryptographic best practices and reducing possible attack vectors to be considered. Note though that no vulnerability was found. #273
* Paywalled resources are now `flask_restful` resources and can be implemented more flexibly as such. This now also properly supports dynamic resource prices. #270
* Refactored contract code to comply with Solidity guidelines. #271
* Updated Docker files to allow examples to be run on the same server. #262
* Fixed an issue where the Python client would still try and open a channel, even if the specified token amount exceeded the available funds. #260
* The HTTP client now supports all HTTP methods that are also supported by the `requests` module. The new `microraiden.requests` module allows for `requests`-like syntax of µRaiden-enabled HTTP requests. #258
* The current contract version is maintained in the README.md. #257
* Changed client-side channel balance management #254:

    A `Channel`'s balance now has to be set via an `update_balance()` call that automatically signs the specified balance.

* Added a contract version check in the channel manager, preventing the use of incompatible contracts. #253
* Removed the Python client's persistent state file. #252

    The Python client now recovers possible earlier channel states from server responses, making a local state file redundant.

* Increased the isolated test coverage for the HTTP client. #251
* Added a new callback `on_http_response` to the HTTP client that is called on every HTTP response #250
* Added recovery features to situations when the channel manager has insufficient funds to dispute a channel closure. #247
* Changed the default behavior of the HTTP client so that it reattempts a certain payment if the server responds with an invalid amount error. #245
* Fixed typos in the README.md. #242
* Added a Travis CI status icon to the README.md. #241
* Fixed a bug in the Python client's channel syncing that resulted from changed argument names of topup events. #239

## 0.1.0 - 2017-12-01 - Bug Bounty Release

Initial release

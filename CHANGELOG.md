# Changelog

## Development
* Added a changelog #356
* Updated Docker files to allow examples to be run on the same server. #262
* Fixed an issue where the Python client would still try and open a channel, even if the specified token amount exceeded the available funds. #260
* The HTTP client now supports all HTTP methods that are also supported by the `requests` module. #258
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
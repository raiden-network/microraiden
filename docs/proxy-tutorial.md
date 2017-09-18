# Introduction

In this tutorial we will create a simple paywalled server that will serve some
static files as well as dynamically generated responses, payable with a
custom token. You can find example code for this tutorial in
`microraiden/examples/echo_server.py`.

# Requirements

Please refer to README.md to install all required dependencies.
You will also need a Chrome browser with the [MetaMask plugin](https://metamask.io/).


# Setting up the proxy

## Initialization

For initialization you will have to supply the following parameters:
- The address of the channel manager contract.
- The private key of the account receiving the payments (to extract it from a
  keystore file you can use MyEtherWallet's "View Wallet Info" functionality).
- A file in which the proxy stores off-chain balance proofs. Set this to a
  path writable by the user that starts the server.

```python
from microraiden.proxy.paywalled_proxy import PaywalledProxy
app = PaywalledProxy(channel_manager_address, private_key, state_file)
```
The channel manager will start syncing with the blockchain immediately.


## Resource types


Now you will have to add some resources. To serve a single static file from
the filesystem, you can use:
```python
from microraiden.proxy.content import PaywalledFile
app.add_content(PaywalledFile("file.txt", 10, "/srv/paywall/content/test.txt"))
```
The file will then be available at the URI `/file.txt`. Only after a payment
of 10 tokens, the proxy will send it back to the user and will try to
set the Content-Type header appropriately. Without payment, the server
responds with `402 Payment Required`.

For dynamic resources, you can use the `PaywalledContent` class:
```python
from microraiden.proxy.content import PaywalledContent
app.add_content(PaywalledContent("teapot.txt", 1, lambda _: ("HI I AM A TEAPOT", 418)))
app.add_content(PaywalledContent("temperature", 2, lambda _: (thermo.get_temp(), 200)))
app.add_content(PaywalledContent("sqrt/^[0-9]+(\.[0-9]+)?$", 3, lambda uri:
	number = float(uri.split('/')[1])
	return (str(number), 200))
))
```
The first argument of the constructor is a resource URI, the second is a
price, and the third is a content generator function. This function can return
both a tuple `(<content>, <http_status_code>)`, or a flask Response class
created by, e.g., a `make_response()` call.

Another possible content type is a URL. This is useful to fetch content
from a remote CDN:
```python
from microraiden.proxy.content import PaywalledProxyUrl
app.add_content(PaywalledProxyUrl("cdn\/.*", 1, "lambda _: 'http://cdn.myhost.com:8000/resource42'"))
```
The constructor arguments are, in order of appearance, a regex defining the
resource URI, a price, and a function that returns a remote URL specifying
where to fetch the content from.


## Setting a price for the resource dynamically

A price argument for the content can not only be a constant integer, but also
a callable. You can exploit that to set the price depending on the requested
resource:
```python
app.add_content(PaywalledContent("reserve_tokens/[0-9]+",
	lambda request: int(request.split("/")[1]),
	lambda _: ("Tokens reserved", 200)))
```


# Starting/stopping the proxy

You start proxy by calling `run()` method. This call is non-blocking -- the
proxy is started as a WSGI greenlet. Use `join()` to sync with the task. This
will block until proxy has stopped. To terminate the server, call stop() from
another greenlet.
```python
app.run(debug=True)
app.join()
```



# Accessing the content

## Browser

To access the content with your browser, navigate to the URL of the resource
you'd like to get. You'll be faced with paywall -- a site requesting you to
pay for the resource. To do so, you first have to open a new channel. If you
have the MetaMask extension installed, you can
set the amount to be deposited to the channel.
After confirming the deposit, you can navigate and payments will be done
automatically.


## Machine-to-machine client

If you would like to get the resource using your own application, you can use
m2m_client class. Please refer to the M2M client documentation and to the client
example (`microraiden/examples/echo_client.py`).


# Side notes


## Proxy state file

Off-chain transactions are stored in a state file that is loaded on start.
You should do regular backups of this file -- it contains balance signatures of
the client, and if you lose them, you will have no way of proving that the
client is settling the channel using less funds than he has actually paid to the
proxy.

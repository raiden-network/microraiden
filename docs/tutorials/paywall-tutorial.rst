Paywall tutorial
########################################

.. toctree::
  :maxdepth: 2

Before starting, please follow the
:doc:`microraiden installation instructions <dev-setup>`
and the
:doc:`instructions to set up geth <blockchain>`.

Introduction
============

In this tutorial we will create a simple paywalled server that will
echo a requested path paramter, payable with a custom token. You can find example code for this tutorial
in ``microraiden/examples/echo_server.py``.

Requirements
============

Please refer to README.md to install all required dependencies. You will
also need a Chrome browser with the `MetaMask
plugin <https://metamask.io/>`__.

Setting up the proxy
====================

.. TODO mention command line options for configuration of e.g. the channel manager contract address

Initialization
--------------

For initialization you will have to supply the following parameters:
  - The **private** key of the account receiving the payments (to extract it from a keystore file you can use MyEtherWallet's "View Wallet Info" functionality).
  - A **file** in which the proxy stores off-chain balance proofs. Set this to a path writable by the user that starts the server.

.. code:: python

    from microraiden.make_helpers import make_paywalled_proxy
    app = make_paywalled_proxy(private_key, state_file_name)

:py:meth:`microraiden.make_helpers.make_paywalled_proxy` is a helper that handles the setup of the channel manager
and returns a :py:class:`microraiden.proxy.paywalled_proxy.PaywalledProxy` instance.
Microraiden also includes other helpers that parse common commandline options. We are not using them in this example - for a quick overview how to use them, 
refer to i.e. :py:meth:`microraiden.examples.demo_proxy.__main__`


.. TODO explain shortly what the channel manager does and link with autodoc

The channel manager will start syncing with the blockchain immediately.

Resource types
--------------

Now we will create a custom resource class that simply echoes a path-parameter of the user's request for a fixed price.
The workflow is the same as with the Flask-restful: Subclass :py:class:`microraiden.proxy.resources.Expensive` and
implement the HTTP methods you want to expose.

.. TODO say something about the interface of the .get method and link to autodoc specs, or to the flask-restful doc

.. code:: python

    from microraiden.proxy.resources import Expensive

    class StaticPriceResource(Expensive):
        def get(self, url: str, param: str):
                log.info('Resource requested: {} with param "{}"'.format(request.url, param))
                return param

We add one static resource to our :py:class:`~microraiden.proxy.paywalled_proxy.PaywalledProxy` instance.
The `url` argument will comply with standard flask routing rules.

.. TODO maybe link to the rules

.. code:: python

    app.add_paywalled_resource(
        cls=StaticPriceResource,
        url="/echofix/<string:param>",
        price=5
    )

The resource will then be available for example at the URI ``/echofix/foo``. Only after a
payment of 5 tokens, the proxy will send the ``foo`` parameter back to the user and will
set the Content-Type header appropriately. Without payment, the
server responds with ``402 Payment Required``.

A probably more useful paywalled resource is a URL. This is useful to fetch content
from a remote CDN:

.. code:: python

    from microraiden.proxy.content import PaywalledProxyUrl

    app.add_paywalled_resource(
        cls=PaywalledProxyUrl,
        url="cdn\/.*",
        resource_class_kwargs={"domain": 'http://cdn.myhost.com:8000/resource42'}
    )

Note, that the kwargs for the constructor of the resource-class (here our :py:class:`~microraiden.proxy.content.PaywalledProxyUrl`)
have to be passed as a dict with the ``resource_class_kwargs`` argument.
In this case, the ``domain`` kwarg is the remote URL specifying where to fetch the content from.


Setting a price for the resource dynamically
--------------------------------------------

We can also construct the Resource in a way that the price will be dynamically calculated, e.g. based on the requests parameters.

.. code:: python

    class DynamicPriceResource(Expensive):
        def get(self, url: str, param: str):
                log.info('Resource requested: {} with param "{}"'.format(request.url, param))
                return param

        def price(self):
                return len(request.view_args['param'])


    app.add_paywalled_resource(
        cls=DynamicPriceResource,
        url="/echodyn/<string:param>",
    )

Here, the price to be paid is the length of the requested string. 
A request of the ``/echodyn/foo`` resource, would therefore require a payment of 3 tokens. 


Starting/stopping the proxy
===========================

You start proxy by calling ``run()`` method. This call is non-blocking
-- the proxy is started as a WSGI greenlet. Use ``join()`` to sync with
the task. This will block until proxy has stopped. To terminate the
server, call stop() from another greenlet.

.. code:: python

    app.run(debug=True)
    app.join()

Accessing the content
=====================

Browser
-------

To access the content with your browser, navigate to the URL of the
resource you'd like to get. You'll be faced with a paywall -- a site
requesting you to pay for the resource. To do so, you first have to open
a new channel. If you have the MetaMask extension installed, you can set
the amount to be deposited to the channel. After confirming the deposit,
you can navigate and payments will be done automatically.


Side notes
==========

Proxy state file
----------------

Off-chain transactions are stored in a sqlite database. You should do
regular backups of this file -- it contains balance signatures of the
client, and if you lose them, you will have no way of proving that the
client is settling the channel using less funds than he has actually
paid to the proxy.

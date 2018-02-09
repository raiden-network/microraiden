.. microraiden documentation master file, created by
   sphinx-quickstart on Thu Dec 21 13:09:59 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to microraiden's documentation!
=======================================

What is µRaiden?
-----------------
µRaiden (read: Micro Raiden) is a payment channel framework for frequent, fast and free ERC20 token based micropayments between two parties. 
It comes as a set of open source libraries, documentation, and code examples for multiple use cases, ready to implement on the Ethereum mainnet. 
Whereas its big brother, the Raiden Network, aims to allow for multihop transfers via a network of bidirectional payment channels, µRaiden already enables to make micropayments through unidirectional payment channels.

Try out the demos
------------------

We have deployed some demo applications that make extensive use of µRaiden in your browser.
Although you need some testnet-Ether and MetaMask, it's a very easy starting point 
to try out µRaiden.
Just follow the instructions on  
https://demo.micro.raiden.network/

Quick Start
------------

-  install the Proxy component (more details
   in the :doc:`tutorials/proxy-tutorial`):

.. code-block:: sh

    virtualenv -p python3 env
    . env/bin/activate
    pip install microraiden

-  install the WebUI component for the paywall examples

Note that while the ``RaidenMicroTransferChannels`` contract supports
multiple open channels between a sender and a receiver, the WebUI
component only supports one.

.. code-block:: sh

    cd microraiden/microraiden/webui/microraiden
    npm i && npm run build

-  run the Proxy component:

.. code-block:: sh

    cd microraiden
    python -m microraiden.examples.demo_proxy --private-key <private_key_file> start

For an overview of parameters and default options check
in the :doc:`cmdline` documentation or directly in the source-code for
:py:mod:`microraiden.microraiden.click_helpers`.

For chain and contract settings change :py:mod:`microraiden.microraiden.config`.

- Go to the paywalled resource pages:
    - http://localhost:5000/teapot

Documentation Content
----------------------

.. toctree::
   :maxdepth: 2 

   introduction/index
   specifications/index
   pyserver/index
   pyclient/index
   jsclient/index
   contract/index 
   tutorials/index


Indices and tables
--------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

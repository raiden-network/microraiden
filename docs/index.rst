.. microraiden documentation master file, created by
   sphinx-quickstart on Thu Dec 21 13:09:59 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to microraiden's documentation!
=======================================

Quick Start
------------

-  install the Proxy component (more details
   in the :doc:`proxy-tutorial`):

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


What is microraiden?
--------------------

.. toctree::
   :maxdepth: 2 

   introduction

Guide
--------------------

.. toctree::
   :maxdepth: 2 

   installation
   cmdline

Tutorials
--------------------

.. toctree::
   :maxdepth: 2

   proxy-tutorial

Development
--------------------

.. toctree::
   :maxdepth: 2 

   dev-overview
   rest-api
   api-reference

JavaScript library
--------------------

.. toctree::
   :maxdepth: 2 

   jsclient/index

Smart Contract  
--------------------

.. toctree::
   :maxdepth: 2 

   contract/index 

Indices and tables
--------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

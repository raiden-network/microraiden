Quick Start
============

-  install the Proxy component (more details
   `here </microraiden/README.md>`__):

.. code-block:: sh

    virtualenv -p python3 env
    . env/bin/activate
    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden/microraiden
    pip install -r requirements-dev.txt
    pip install -e .

-  install the WebUI component for the paywall examples

Note that while the ``RaidenMicroTransferChannels`` contract supports
multiple open channels between a sender and a receiver, the WebUI
component only supports one.

.. code-block:: sh

    cd microraiden/microraiden/webui/microraiden
    npm i && npm run build

-  run the Proxy component (more details
   `here </microraiden/README.md>`__):

For an overview of parameters and default options check
:func:`microraiden.microraiden.click_helpers.py`

For chain and contract settings change:
https://github.com/raiden-network/microraiden/blob/master/microraiden/microraiden/config.py
This is where you integrate custom contract & token deployments.

.. code-block:: sh 

    cd microraiden
    python -m microraiden.examples.demo_proxy --private-key <private_key_file> start

-  Go to the paywalled resource pages:

   -  http://localhost:5000/doggo.jpg


You can use the configuration for the above default example for creating
your own payment channel service.

-  Proxy: `/docs/proxy-tutorial.md </docs/proxy-tutorial.md>`__
-  Web Interface: soon
-  Various paywall `examples </microraiden/microraiden/examples>`__


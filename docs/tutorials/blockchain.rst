Blockchain setup
=================

In order to follow our tutorials or develop your own µRaiden applications,
there are some additional requirements to be fullfilled.
If you want to develop applications that function as the **Receiver** you have
to connect to the Ethereum blockchain through one of the Ethereum node applications.
There are others, but we focus on `geth`, the Go implementation.

Running `geth`
---------------

The following components have to be installed in order to run the tutorials:

Geth must be up and running, listening on RPC 8545 and completely synced with Ropsten
Optional: To create an account, get Ropsten ETH (RETH) and export the private key, MetaMask must be installed and connected to Ropsten
Optional: To use the echo_client, you have to acquire TKN. On the main page (https://github.com/raiden-network/microraiden) the Token addresses are listed, for Ropsten it can be found `here <https://ropsten.etherscan.io/address/0xff24d15afb9eb080c089053be99881dd18aa190>`_
Setup a Ropsten-synced Geth

The quick start requires that your Geth client is synced to the Ropsten testnet.
Geth should answer RPC calls on `http://localhost:8545` and have the APIs `eth`, `net`, `web3` and `personal` accessible. 

Note: as of Geth version `1.8.0`, these parameters are required to start Geth in the correct mode:

.. code:: sh

   geth --testnet --syncmode "fast" \ 
        --rpc --rpcapi eth,net,web3,personal \
        --cache=1024 \ 
        --rpcport 8545 --rpcaddr 127.0.0.1 \
        --rpccorsdomain "*"


Funded Ropsten account with MetaMask
---------------------------------------

Note: You don’t have to follow these steps if you have an account on Ropsten already preloaded with Ropsten Ether and know how to export the private key of the preloaded account.

After successful installation of MetaMask, just follow the steps mentioned in the screenshots to create a new account, get Ropsten Ether at a faucet and export the private key of this new, Ether preloaded account.
We will use the private key for js-Client applications in the Tutorials.
Your MetaMask account will represent the **Sender** of a microtransaction.


.. figure:: /diagrams/metamask.png
   :scale: 50
   :alt:


.. figure:: /diagrams/metamask2.png
   :scale: 50
   :alt:


Buy TKN on Ropsten
-------------------

To be able to use the echo client, you have to get the “TKN” Token configured for the RaidenMicroTransferChannels on Ropsten.

With our demo app
~~~~~~~~~~~~~~~~~~~~~~~~~~
The easiest way to get same TKN on the Ropsten-network is to use our JavaScript application
that we host with our µRaiden `live-demos <https://demo.micro.raiden.network>`_.

Altough this is part of a specific demo-application, you can just use the upper part of the dialogue 
and forget about the lower half.


1) Choose the browser with your Ropsten-ETH loaded MetaMask account activated
2) visit e.g. the fortune cookie demo `here <https://demo.micro.raiden.network/fortunes_en>`_
3) Click on `Buy` to exchange your RopstenETH (RETH) for TKN (in 50 TKN increments)

.. figure:: /diagrams/buytkndemo.png
   :alt:


A dialogue will pop up in MetaMask that asks for your confirmation of the generated transaction.

4) Accept the transaction


To check wether the exchange of TKN was sucessful, you can add TKN as a custom token to MetaMask.

5) Under the `Tokens` tab, choose `Add token` and fill in the TKN address again:

.. code::

        0xFF24D15afb9Eb080c089053be99881dd18aa1090


.. figure:: /diagrams/myether4.png
   :alt:

6) Once the transaction was succesful, you should see your TKN balance under the `Tokens` tab

.. figure:: /diagrams/myether5.png
   :alt:


 

With  MyEtherWallet
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to have a little bit more control over the token-exchange,
you can also use MyEtherWallet to interact with the Smart-Contract directly:

.. TODO add picture for point 3
1) Choose the browser with your Ropsten-ETH loaded MetaMask account activated
2) Go to https://www.myetherwallet.com/ and go through their advice on phishing-precautions.
3) Select the `Ropsten` Network in the tab in the upper right
4) click on the Contracts tab and fill in the contract address:

.. code::

        0xFF24D15afb9Eb080c089053be99881dd18aa1090

5) fill in the ABI field with the data you get `here <http://api-ropsten.etherscan.io/api?module=contract&action=getabi&address=0xFF24D15afb9Eb080c089053be99881dd18aa1090&format=raw>`_:

.. figure:: /diagrams/myether1.png
   :alt:

6) Choose the `mint` function and use MetaMask to access your wallet


.. figure:: /diagrams/myether2.png
   :alt:

7) put in an amount of RopstenETH (RETH) you want to exchange for TKN (0.1 RETH will get you 50 TKN)

.. figure:: /diagrams/myether3.png
   :alt:

A dialogue will pop up in MetaMask that asks for your confirmation of the generated transaction.

8) Accept the transaction


To check wether the exchange of TKN was sucessful, you can add TKN as a custom token to MetaMask.

9) Under the `Tokens` tab, choose `Add token` and fill in the TKN address again:

.. code::

        0xFF24D15afb9Eb080c089053be99881dd18aa1090


.. figure:: /diagrams/myether4.png
   :alt:

10) Once the transaction was succesful, you should see your TKN balance under the `Tokens` tab

.. figure:: /diagrams/myether5.png
   :alt:



**Now you're good to go! Check out the other Tutorials and get started with microraiden!**

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

.. figure:: /diagrams/uRaidenOverview.png
   :alt:

Try out the demos
------------------

We have deployed some demo applications that make extensive use of µRaiden in your browser.
Although you need some testnet-Ether and MetaMask, it's a very easy starting point 
to try out µRaiden.
Just follow the instructions on  
https://demo.micro.raiden.network/

Next steps
-----------
If you want to start playing with microraiden, a good starting point is to check out the :doc:`Tutorials <tutorials/index>` section.
Best you start with the :doc:`developer setup <tutorials/index>` and try our :doc:`Blockchain Tutorial <tutorials/index>` afterwards.

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

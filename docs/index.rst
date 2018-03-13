.. microraiden documentation master file, created by
   sphinx-quickstart on Thu Dec 21 13:09:59 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to µRaiden's documentation!
=======================================

What is µRaiden?
-----------------
µRaiden (read: Micro Raiden) is a payment channel framework for frequent, fast and free ERC20 token based micropayments between two parties. 
It comes as a set of open source libraries, documentation, and code examples for multiple use cases, ready to implement on the Ethereum mainnet. 
Whereas its big brother, the `Raiden Network <http://raiden.network>`_, aims to allow for multihop transfers via a network of bidirectional payment channels, µRaiden already enables to make micropayments through unidirectional payment channels.

.. figure:: /diagrams/uRaidenOverview.png

   Schematic overview of an exemplaric µRaiden application [1]_ [3]_

Try out the demos
------------------

We have deployed some demo applications that make extensive use of µRaiden in your browser.
Although you need some testnet-Ether and MetaMask, it's a very easy starting point 
to try out µRaiden.
Just follow the instructions on https://demo.micro.raiden.network/

Next steps
-----------
If you want to start playing with µRaiden, a good starting point is to check out the :doc:`Tutorials <tutorials/index>` section.
Best you start with the :doc:`developer setup <tutorials/index>` and continue with our :doc:`Blockchain Tutorial <tutorials/index>`.

Documentation Content
----------------------

.. toctree::
   :maxdepth: 3

   introduction/index
   tutorials/index
   applications/index
   contract/index 
   specifications/index


Indices and tables
--------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. rubric:: Footnotes

.. [#] All robot icons made by `Freepic <http://flaticon.com/authors/freepik>`_ from http://www.flaticon.com.
.. [#] Raspberry PI Pictograms by `TinkTank.club <http://www.tinktank.club>`_
.. [#] All other icons from http://icomoon.io IcoMoon Icon Pack Free, licensed under a Creative Commons Attribution 4.0 International License


M2M-Client (python)
===================

The M2M-Client is a Python framework for building applications that run on the payment-senders machine.
The client interacts with the blockchain to handle channel creation and closing when needed.
It communicates with a payment-receivers http-endpoint (e.g. implemented with our
:doc:`Python server framework </applications/pyserver/index>`) and handles the signing of off-chain transactions.

In order to implement an automated machine-to-machine interaction, the framework provides event-handler methods,
that allow to easily write extension classes to handle the clients business-logic without user interaction.



.. toctree::
   :maxdepth: 2 

   installation
   usage

   components-overview
   py-api



Development overview
########################################

.. toctree::
  :maxdepth: 4 

µRaiden components overview. ! Some parts might be outdated.


HTTP Headers
-----------------------------------

Encoding: 

.. TODO: find out int-size, add address fixed size, if relevant  

-  ``address``:  ``0x`` prefixed hex encoded 
-  ``uint``: ``[0-9]`` 
-  ``bytes``: ``0x`` prefixed hex encoded

Response Headers
~~~~~~~~~~~~~~~~

200 OK
^^^^^^

+------------------------+-----------+---------------------------------------------+
|       Headers          |   Type    |   Description                               |
+========================+===========+=============================================+
| RDN-Gateway-Path       | bytes     | Path root of the channel management app     |
+------------------------+-----------+---------------------------------------------+
| RDN-Cost               | uint      | Cost of the payment                         |
+------------------------+-----------+---------------------------------------------+
| RDN-Contract-Address   | address   | Address of MicroTransferChannels contract   |
+------------------------+-----------+---------------------------------------------+
| RDN-Receiver-Address   | address   | Address of the Merchant                     |
+------------------------+-----------+---------------------------------------------+
| RDN-Sender-Address     | address   | Address of the Client                       |
+------------------------+-----------+---------------------------------------------+
| RDN-Sender-Balance     | uint      | Balance of the Channel                      |
+------------------------+-----------+---------------------------------------------+

402 Payment Required
^^^^^^^^^^^^^^^^^^^^

+------------------------+-----------+---------------------------------------------+
|       Headers          |   Type    |   Description                               |
+========================+===========+=============================================+
| RDN-Gateway-Path       | bytes     | Path root of the channel management app     |
+------------------------+-----------+---------------------------------------------+
| RDN-Price              | uint      | The price of answering the request          |
+------------------------+-----------+---------------------------------------------+
| RDN-Contract-Address   | address   | Address of MicroTransferChannels contract   |
+------------------------+-----------+---------------------------------------------+
| RDN-Receiver-Address   | address   | Address of the Merchant                     |
+------------------------+-----------+---------------------------------------------+

402 Payment Required (non accepted RDN-Balance-Signature )
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------------+----------+-------------------------------------------+
|       Headers         |   Type   |   Description                             |
+=======================+==========+===========================================+
| RDN-Gateway-Path      | bytes    | Path root of the channel management app   |
+-----------------------+----------+-------------------------------------------+
| RDN-Price             | uint     | The price of answering the request        |
+-----------------------+----------+-------------------------------------------+
| RDN-Contract-Address  | address  | Address of MicroTransferChannels contract |
+-----------------------+----------+-------------------------------------------+
| RDN-Receiver-Address  | address  | Address of the Merchant                   |
+-----------------------+----------+-------------------------------------------+
| RDN-Sender-Address    | address  | Address of the Client                     |
+-----------------------+----------+-------------------------------------------+
| RDN-Sender-Balance    | uint     | Balance of the Channel                    |
+-----------------------+----------+-------------------------------------------+
| RDN-Insufficient-Fund | uint     | Failure - either Payment value too low or |
| s                     |          | balance exceeds deposit                   |
+-----------------------+----------+-------------------------------------------+
| RDN-Insufficient-Conf | uint     | Failure - not enough confirmations after  |
| irmations             |          | the channel creation. Client should wait  |
|                       |          | and retry.                                |
+-----------------------+----------+-------------------------------------------+

4xx / 5xx Errors
^^^^^^^^^^^^^^^^

Refund.

Request Headers
~~~~~~~~~~~~~~~

+-----------------------+----------+-------------------------------------------+
|       Headers         |   Type   |   Description                             |
+=======================+==========+===========================================+
| RDN-Contract-Address  | address  | Address of MicroTransferChannels contract |
+-----------------------+----------+-------------------------------------------+
| RDN-Receiver-Address  | address  | Address of the Merchant                   |
+-----------------------+----------+-------------------------------------------+
| RDN-Sender-Address    | address  | Address of the Client                     |
+-----------------------+----------+-------------------------------------------+
| RDN-Payment           | uint     | Amount of the payment                     |
+-----------------------+----------+-------------------------------------------+
| RDN-Sender-Balance    | uint     | Balance of the Channel                    |
+-----------------------+----------+-------------------------------------------+
| RDN-Balance-Signature | bytes    | Signature from the Sender, signing the    |
|                       |          | balance (post payment)                    |
+-----------------------+----------+-------------------------------------------+
| RDN-Open-Block        | uint     | Opening block number of the channel       |
|                       |          | required for unique identification        |
+-----------------------+----------+-------------------------------------------+

Exceptions
----------

::


    InvalidBalanceAmount
    InvalidBalanceProof
    NoOpenChannel
    InsufficientConfirmations
    NoBalanceProofReceived
    StateContractAddrMismatch
    StateReceiverAddrMismatch

Off-Chain Messages
------------------

Micropayment Sequence
~~~~~~~~~~~~~~~~~~~~~

(not-so-standard sequence diagram) For a better overview, also check out
how the smart contract does a :ref:`balance-proof validation <contract-validate-balance-proof>`.

.. figure:: /diagrams/OffChainSequence.png
   :alt: 

Channel Closing Sequence
~~~~~~~~~~~~~~~~~~~~~~~~

For a better overview, also check out how the smart contract does a
:ref:`closing signature validation <contract-validate-close>`.

.. figure:: /diagrams/OffChainSequenceClosing.png
   :alt: 

Proxy
-----

Channel manager
~~~~~~~~~~~~~~~

.. figure:: /diagrams/ChannelManagerClass.png
   :alt: 

Paywalled Proxy
~~~~~~~~~~~~~~~

.. figure:: /diagrams/PaywalledProxyClass.png
   :alt: 

Python Client
-------------

.. figure:: /diagrams/PythonClientClass.png
   :alt: 

Web Client
-----------
For an overview of development regarding the smart contracts, please refer to the :doc:`jsclient/index` documentation.

Smart Contract
---------------
For an overview of development regarding the smart contracts, please refer to the :ref:`Smart Contract API <contract-development>` documentation.


HTTP Headers
-----------------------------------

Response Headers
~~~~~~~~~~~~~~~~

200 OK
^^^^^^

+------------------------+-----------+-------------------------------------------------+
|       Headers          |   Type    |   Description                                   |
+========================+===========+=================================================+
| RDN-Gateway-Path       | bytes     | Path root of the channel management app         |
+------------------------+-----------+-------------------------------------------------+
| RDN-Receiver-Address   | address   | Address of the Merchant                         |
+------------------------+-----------+-------------------------------------------------+
| RDN-Contract-Address   | address   | Address of RaidenMicroTransferChannels contract |
+------------------------+-----------+-------------------------------------------------+
| RDN-Token-Address      | address   | Address of the Token contract                   |
+------------------------+-----------+-------------------------------------------------+
| RDN-Price              | uint      | Resource price                                  |
+------------------------+-----------+-------------------------------------------------+
| RDN-Sender-Address     | address   | Address of the Client                           |
+------------------------+-----------+-------------------------------------------------+
| RDN-Sender-Balance     | uint      | Balance of the Channel                          |
+------------------------+-----------+-------------------------------------------------+

402 Payment Required
^^^^^^^^^^^^^^^^^^^^

+------------------------+-----------+-------------------------------------------------+
|       Headers          |   Type    |   Description                                   |
+========================+===========+=================================================+
| RDN-Gateway-Path       | bytes     | Path root of the channel management app         |
+------------------------+-----------+-------------------------------------------------+
| RDN-Receiver-Address   | address   | Address of the Merchant                         |
+------------------------+-----------+-------------------------------------------------+
| RDN-Contract-Address   | address   | Address of RaidenMicroTransferChannels contract |
+------------------------+-----------+-------------------------------------------------+
| RDN-Token-Address      | address   | Address of the Token contract                   |
+------------------------+-----------+-------------------------------------------------+
| RDN-Price              | uint      | Resource price                                  |
+------------------------+-----------+-------------------------------------------------+
| RDN-Sender-Address     | address   | Address of the Client                           |
+------------------------+-----------+-------------------------------------------------+
| RDN-Sender-Balance     | uint      | Balance of the Channel                          |
+------------------------+-----------+-------------------------------------------------+
| RDN-Balance-Signature  | bytes     | Optional. Last saved balance proof from the     |
|                        |           | sender.                                         |
+------------------------+-----------+-------------------------------------------------+
|                        |           | **+ one of the following:**                     |
+------------------------+-----------+-------------------------------------------------+
| RDN-Insufficient-Conf  | uint      | Failure - not enough confirmations after the    |
| irmations              |           | channel creation. Client should wait and retry. |
+------------------------+-----------+-------------------------------------------------+
| RDN-Nonexisting-Channel| string    | Failure - channel does not exist or was closed. |
+------------------------+-----------+-------------------------------------------------+
| RDN-Invalid-Balance-   | uint      | Failure - Balance must not be greater than      |
| Proof                  |           | deposit or The balance must not decrease.       |
+------------------------+-----------+-------------------------------------------------+
| RDN-Invalid-Amount     | uint      | Failure - wrong payment value                   |
+------------------------+-----------+-------------------------------------------------+

409
^^^^^^^^^^^^^^^^

- ValueError

502
^^^^^^^^^^^^^^^^

- Ethereum node is not responding
- Channel manager ETH balance is below limit

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

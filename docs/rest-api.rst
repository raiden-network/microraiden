REST API
############# 

.. toctree::
  :maxdepth: 3


Introduction
============

µRaiden exposes a Restful API to
provide insight into a channel state, balances, and it allows proxy
operator to close and settle the channels.

Following are the available API endpoints with which you can interact
with RMS.

Proxy endpoints
===============

Getting the status of the proxy
-------------------------------

This will return a status of balances, open channels etc.

- **deposit\_sum** - sum of all open channel deposits
- **open\_channels** - count of all open channels
- **pending\_channels** - count of all closed, but not yet settled channels 
- **balance\_sum** - sum of all spent, but not yet settled funds 
- **unique\_senders** - count of all unique addresses that have channels open 
- **liquid\_balance** - amount of tokens that are settled and available to the receiver 
- **token\_address** - token contract address
- **contract\_address** - channel manager contract address 
- **receiver\_address** - server's ethereum address 
- **manager\_abi** - ABI of the channel manager contract 
- **token\_abi** - ABI of the token contract

Example Request
^^^^^^^^^^^^^^^^
``GET /api/1/stats``

Example Response 
^^^^^^^^^^^^^^^^
``200 OK`` and

.. code-block:: json

    {
      "deposit_sum": "268",
      "open_channels": "33",
      "pending_channels": "15",
      "balance_sum": "12",
      "unique_senders": "6",
      "liquid_balance": "334",
      "token_address" : "0x8227a53130c90d32e0294cdde576411379138ba8",
      "contract_address": "0x69f8b894d89fb7c4f6f082f4eb84b2b2c3311605",
      "receiver_address": "0xe67104491127e419064335ea5bf714622a209660",
      "manager_abi": "{ ... }",
      "token_abi": "{ ... }",
    }

Channel endpoints
=================

Getting all open channels
-------------------------

This will return a list of all open channels.

Example Request
^^^^^^^^^^^^^^^^

``GET /api/1/channels``

Example Response
^^^^^^^^^^^^^^^^

``200 OK`` and

.. code-block:: json

    [
    {
        "sender_address" : "0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb",
        "open_block"  : "3241462",
        "balance"     : "0",
        "deposit"     : "10",
    },
    {
        "sender_address" : "0x5176305093fff279697d3fc9b6bc09574303edb4",
        "open_block"  : "32654234",
        "balance"     : "0",
        "deposit"     : "25",
    },
    ]

Getting all open channels for a given sender
--------------------------------------------

This will return a list of all open channels for the sender specified in
the second argument of the URL.

Example Request
^^^^^^^^^^^^^^^^

``GET /api/1/channels/<sender_address>``

Example Response 
^^^^^^^^^^^^^^^^

``200 OK`` and

.. code-block:: json

    [
    {
        "sender_address" : "0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb",
        "open_block"  : "3241462",
        "balance"     : "0",
        "deposit"     : "10",
        "state"       : "open",
    },
    ]

Getting a single channel info
-----------------------------

Return an info about the channel, identified by sender and open block
id.

Example Request
^^^^^^^^^^^^^^^^

``GET /api/1/channels/<sender_address>/<open_block>``

Example Response 
^^^^^^^^^^^^^^^^

``200 OK`` and

.. code-block:: json

    {
        "sender_address" : "0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb",
        "open_block"  : "3241462",
        "balance"     : "0",
        "deposit"     : "10",
        "state"       : "open",
    }

Cooperatively closing a channel
-------------------------------

Returns a receiver's signature that can be used to settle the channel
immediately.

Example Request
^^^^^^^^^^^^^^^^
``DELETE /api/1/channels/<sender_address>/<open_block>``

with payload

.. code-block:: json

    {
        "signature": "0x9d735db00d72afdba4d144bab4fd9280a3cc2e75d8ad1272ad1e9da0b6eb110e5c810e9148c07312d71e791beabea4c756c973d70d863b81b1a32854b632975711",
    }

Example Response 
^^^^^^^^^^^^^^^^
``200 OK`` and

.. code-block:: json

    {
        "close_signature" : "0xb30809f9a32e4f5012a3e7a7275e4f0f96eaff49f7a34747507abc3147a0975c31cf9f9aa318d1f9675d6e39f062a565213bcef4baa820f0332616f0c38324fe01",
    }

Possible Responses
^^^^^^^^^^^^^^^^^^

+---------------------+-------------------------------+
| HTTP Code           | Condition                     |
+=====================+===============================+
| 200 OK              | For a successful coop-close   |
+---------------------+-------------------------------+
| 500 Server Error    | Internal Raiden node error    |
+---------------------+-------------------------------+
| 400 Bad request     | Invalid address, signature,   |
|                     | or channel doesn't exist.     |
+---------------------+-------------------------------+


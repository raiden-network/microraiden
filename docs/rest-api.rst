REST API
############# 

.. toctree::
  :maxdepth: 3


Introduction
============

µRaiden exposes a Restful API to
provide insight into a channel state, balances, and it allows proxy
operator to close and settle the channels.

Proxy endpoints
===============

Getting the status of the proxy
-------------------------------

``/api/1/stats``

Return proxy status: balances, open channels, contract ABI etc.

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

``/api/1/channels/``

Return a list of all open channels.

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

``/api/1/channels/<sender_address>``

Return a list of all open channels for the sender specified in
the second argument of the URL.

Example Request
^^^^^^^^^^^^^^^^

``GET /api/1/channels/0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb``

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

``/api/1/channels/<sender_address>/<open_block>``

Return an info about the channel, identified by sender and open block
id.

Example Request
^^^^^^^^^^^^^^^^

``GET /api/1/channels/0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb/3241462``

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

``/api/1/channels/<sender_address>/<open_block>``

Return a receiver's signature that can be used to settle the channel
immediately (by calling contract's `cooperativeClose()` function).

Example Request
^^^^^^^^^^^^^^^^
``DELETE /api/1/channels/0x5601ea8445a5d96eeebf89a67c4199fbb7a43fbb/3241642``

with payload balance - last balance of the channel

.. code-block:: json

    {
        "balance": 13000,
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


Smart Contract
==========================================

Smart Contracts, Unittests and Infrastructure for RaidenPaymentChannel

.. toctree::

   self 


Installation
------------

The Smart Contracts can be installed separately from the other
components.

Prerequisites
~~~~~~~~~~~~~

-  Python 3.6
-  `pip <https://pip.pypa.io/en/stable/>`__

Setup
~~~~~

.. code:: sh


    pip install -r requirements.txt

Usage
~~~~~

-  from ``root/contracts``:

.. code:: sh


    # compilation
    populus compile

    # tests
    pytest
    pytest -p no:warnings -s
    pytest tests/test_uraiden.py -p no:warnings -s

    # Recommended for speed:
    # you have to comment lines in tests/conftest.py to use this
    pip install pytest-xdist==1.17.1
    pytest -p no:warnings -s -n NUM_OF_CPUs

Deployment
~~~~~~~~~~

Chain setup for testing
^^^^^^^^^^^^^^^^^^^^^^^

Note - you can change RPC/IPC chain connection, timeout parameters etc. in `project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json>`__ 


**privtest**
""""""""""""""

1) Start the geth-node from the commandline:
          
  .. code-block:: sh

    geth --ipcpath="~/Library/Ethereum/privtest/geth.ipc" \
         --datadir="~/Library/Ethereum/privtest" \
         --dev \
         ---rpc --rpccorsdomain '\*' --rpcport 8545 \
         --rpcapi eth,net,web3,personal \
         --unlock 0xf590ee24CbFB67d1ca212e21294f967130909A5a \
         --password ~/password.txt

    # geth console 
    # you have to mine yourself: miner.start() 
    geth attach ipc:/Users/loredana/Library/Ethereum/privtest/geth.ipc


**kovan**
"""""""""""""""""

1. Get some testnet-Ether at the `kovan-faucet <https://gitter.im/kovan-testnet/faucet>`__
#. Modify the `project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json#L179>`__ to change the default account

#. Start the `Parity <https://github.com/paritytech/parity>`__ node from the commandline:

  .. code-block:: sh

     parity --geth \
            --chain kovan \
            --force-ui --reseal-min-period 0 \
            --jsonrpc-cors http://localhost \
            --jsonrpc-apis web3,eth,net,parity,traces,rpc,personal \
            --unlock 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb \
            --password ~/password.txt \
            --author 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb

**ropsten**
""""""""""""

1. Get some testnet-Ether at the `ropsten-faucet <https://www.reddit.com/r/ethdev/comments/61zdn8/if\_you\_need\_some\_ropsten\_testnet\_ethers/>`__
#. Modify the `project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json#L49>`__ to change the default account
#. Start the geth node from the commandline:

.. code-block:: sh

  geth --testnet \
       --rpc --rpcport 8545 \
       --unlock 0xbB5AEb01acF5b75bc36eC01f5137Dd2728FbE983 \
       --password ~/password.txt


**rinkeby**
""""""""""""

1. Get some testnet-Ether at the `rinkeby-faucet <https://www.rinkeby.io/#faucet>`__
#. Modify the `/contracts/project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json#L214>`__ to change the default account


**Fast deployment**
""""""""""""""""""""""

There are some scripts to provide you with convenient ways to setup a quick deployment.

  .. code-block:: sh
  
     # Fast deploy on kovan | ropsten | rinkeby | tester | privtest
  
     # Following two calls are equivalent
     python -m deploy.deploy_testnet  # --owner is web.eth.accounts[0]
     python -m deploy.deploy_testnet \
       --chain kovan \
       --owner 0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb \
       --challenge-period 500 \
       --token-name CustomToken --token-symbol TKN \
       --supply 10000000 --token-decimals 18 
  
     # Provide a custom deployed token
     python -m deploy.deploy_testnet --token-address TOKEN_ADDRESS

.. _contract-development:

API
---

Generated docs
~~~~~~~~~~~~~~

.. _Auto-Generated-API: https://github.com/raiden-network/microraiden/blob/master/docs/contract/RaidenMicroTransferChannels.md

There is an Auto-Generated-API_, that is compiled with `soldocs`.


Prerequisites

::

    pip install soldocs
    populus compile
    soldocs --input build/contracts.json --output docs/contract/RaidenMicroTransferChannels.md --contracts RaidenMicroTransferChannels


Opening a transfer channel
~~~~~~~~~~~~~~~~~~~~~~~~~~

ERC223 compatible (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sender sends tokens to the Contract, with a payload for calling
``createChannelPrivate``.

::

    Token.transfer(_to, _value, _data)

Gas cost (testing): 88976

-  ``_to`` = ``Contract.address``
-  ``_value`` = deposit value (number of tokens)
-  ``_data`` contains the Sender and Receiver addresses encoded in 20 bytes
-  in python ``_data = bytes.fromhex(sender_address[2:] + receiver_address[2:])``

.. figure:: diagrams/ChannelOpen_223.png

ERC20 compatible
^^^^^^^^^^^^^^^^

.. code:: py

    # approve token transfers to the contract from the Sender's behalf
    Token.approve(contract, deposit)

    Contract.createChannel(receiver_address, deposit)

Gas cost (testing): 120090

.. figure:: diagrams/ChannelOpen_20.png

Topping up a channel
~~~~~~~~~~~~~~~~~~~~

Adding tokens to an already opened channel.

ERC223 compatible (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sender sends tokens to the Contract, with a payload for calling
``topUp``.

::

    Token.transfer(_to, _value, _data)

Gas cost (testing): 54885

-  ``_to`` = ``Contract.address``
-  ``_value`` = deposit value (number of tokens)
-  ``_data`` contains the Sender and Receiver addresses encoded in 20 bytes + the
   open\_block\_number in 4 bytes
-  in python

.. code:: py

    _data = sender_address[2:] + receiver_address[2:] + hex(open_block_number)[2:].zfill(8)
    _data = bytes.fromhex(_data)

.. figure:: diagrams/ChannelTopUp_223.png

ERC20 compatible
^^^^^^^^^^^^^^^^

.. code:: py

    #approve token transfers to the contract from the Sender's behalf
    Token.approve(contract, added_deposit)

    # open_block_number = block number at which the channel was opened
    Contract.topUp(receiver_address, open_block_number, added_deposit)

Gas cost (testing): 85414

.. figure:: diagrams/ChannelTopUp_20.png

.. _contract-validate-balance-proof:

Generating and validating a balance proof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(to be updated post EIP712)

.. code:: python


    # Sender has to provide a balance proof to the Receiver when making a micropayment
    # The contract implements some helper functions for that

    # Balance message
    bytes32 balance_message_hash = keccak256(
        keccak256(
            'string message_id',
            'address receiver',
            'uint32 block_created',
            'uint192 balance',
            'address contract'
        ),
        keccak256(
            'Sender balance proof signature',
            _receiver_address,
            _open_block_number,
            _balance,
            address(this)
        )
    );

    # balance_message_hash is signed by the Sender with MetaMask
    balance_msg_sig

    # Data is sent to the Receiver (receiver, open_block_number, balance, balance_msg_sig)

.. _contract-validate-close:

Generating and validating a closing agreement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from eth_utils import encode_hex

    # Sender has to provide a balance proof to the Contract and
    # a closing agreement proof from Receiver (closing_sig)
    # closing_sig is created in the same way as balance_msg_sig, but it is signed by the Receiver

    # Closing signature message
    bytes32 balance_message_hash = keccak256(
        keccak256(
            'string message_id',
            'address sender',
            'uint32 block_created',
            'uint192 balance',
            'address contract'
        ),
        keccak256(
            'Receiver closing signature',
            _sender_address,
            _open_block_number,
            _balance,
            address(this)
        )
    );

    # balance_message_hash is signed by the Sender with MetaMask
    balance_msg_sig

    # balance_msg_sig is signed by the Receiver inside the microraiden code
    closing_sig

    # Send to the Contract (example of collaborative closing, transaction sent by Sender)
    Contract.transact({ "from": Sender }).cooperativeClose(
        _receiver_address,
        _open_block_number,
        _balance,
        _balance_msg_sig,
        _closing_sig
    )

Balance proof / closing agreement signature verification:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python


    sender_address = Contract.call().extractBalanceProofSignature(receiver_address, open_block_number, balance, balance_msg_sig)

    receiver_address = Contract.call().extractClosingSignature(sender_address, open_block_number, balance, closing_sig)


Closing a channel
~~~~~~~~~~~~~~~~~

.. code:: py

    # 1. Receiver calls Contract with the sender's signed balance message = instant close & settle
    # 2. Client calls Contract with receiver's closing signature = instant close & settle
    # Gas cost (testing): 71182
    Contract.cooperativeClose(receiver_address, open_block_number, balance, balance_msg_sig, closing_sig)

    # 3. Client calls Contract without receiver's closing signature = challenge period starts, channel is not settled yet
    # Gas cost (testing): 53876
    Contract.uncooperativeClose(receiver_address, open_block_number, balance)

    # 3.a. During the challenge period, 1. can happen.

    # 3.b. Client calls Contract after settlement period ends
    # Gas cost (testing): 40896
    Contract.settle(receiver_address, open_block_number)


.. figure:: diagrams/ChannelCycle.png

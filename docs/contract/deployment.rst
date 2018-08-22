Deployment
==========

Chain setup for testing
-----------------------

Note - you can change RPC/IPC chain connection, timeout parameters etc. in `contracts/project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json>`__


**privtest**
~~~~~~~~~~~~

1) Start the geth-node from the commandline:
          
.. code-block:: sh

    geth --ipcpath="~/Library/Ethereum/privtest/geth.ipc" \
         --datadir="~/Library/Ethereum/privtest" \
        --dev \
        ---rpc --rpccorsdomain '\*' --rpcport 8545 \
        --rpcapi eth,net,web3,personal \
        --unlock 0xf590ee24CbFB67d1ca212e21294f967130909A5a \
        --password ~/password.txt

    # the geth console will show up
    # you have to mine yourself:
    miner.start()
    geth attach ipc:~/Library/Ethereum/privtest/geth.ipc

The :code:`--unlock` argument specifies which geth account should be unlocked for RPC access.
This assumes that :code:`0xf590ee24CbFB67d1ca212e21294f967130909A5a` is your account's address, and has to be changed accordingly.
More info can be found `here <https://github.com/ethereum/go-ethereum/wiki/Managing-your-accounts#listing-accounts-and-checking-balances>`_.

The :code:`--password` argument specifies the file that contains the passphrase the geth account has been locked with.
The :code:`~/password.txt` file has to be changed accordingly to your password file location.
More info can be found `here <https://github.com/ethereum/go-ethereum/wiki/Managing-your-accounts#listing-accounts-and-checking-balances>`_.

**kovan**
~~~~~~~~~

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


The :code:`--unlock` argument specifies which parity account should be unlocked for RPC access.
This assumes that :code:`0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb` is your account's address, and has to be changed accordingly.
More info can be found `here <https://github.com/paritytech/parity/wiki/Configuring-Parity#cli-options>`_.

The :code:`--password` argument specifies the file that contains the passphrase the geth account has been locked with.
The :code:`~/password.txt` file has to be changed accordingly to your password file location.
More info can be found `here <https://github.com/paritytech/parity/wiki/Configuring-Parity#cli-options>`_.

The :code:`--author` argument specifies what the *coinbase* address should be. Set this to the same address as with the :code:`--unlock` argument.
This assumes that :code:`0x5601Ea8445A5d96EEeBF89A67C4199FbB7a43Fbb` is your account's address, and has to be changed accordingly.
More info can be found `here <https://github.com/paritytech/parity/wiki/Configuring-Parity#cli-options>`_.

**ropsten**
~~~~~~~~~~~

1. Get some testnet-Ether at the `ropsten-faucet <https://www.reddit.com/r/ethdev/comments/61zdn8/if\_you\_need\_some\_ropsten\_testnet\_ethers/>`__
#. Modify the `project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json#L49>`__ to change the default account
#. Start the geth node from the commandline:

.. code-block:: sh

  geth --testnet \
       --rpc --rpcport 8545 \
       --unlock 0xf590ee24CbFB67d1ca212e21294f967130909A5a \
       --password ~/password.txt

The :code:`--unlock` argument specifies which geth account should be unlocked for RPC access.
This assumes that :code:`0xf590ee24CbFB67d1ca212e21294f967130909A5a` is your account's address, and has to be changed accordingly.
More info can be found `here <https://github.com/ethereum/go-ethereum/wiki/Managing-your-accounts#listing-accounts-and-checking-balances>`_.

The :code:`--password` argument specifies the file that contains the passphrase the geth account has been locked with.
The :code:`~/password.txt` file has to be changed accordingly to your password file location.
More info can be found `here <https://github.com/ethereum/go-ethereum/wiki/Managing-your-accounts#listing-accounts-and-checking-balances>`_.


**rinkeby**
~~~~~~~~~~~

1. Get some testnet-Ether at the `rinkeby-faucet <https://www.rinkeby.io/#faucet>`__
#. Modify the `/contracts/project.json <https://github.com/raiden-network/microraiden/blob/master/contracts/project.json#L214>`__ to change the default account


**Fast deployment**
~~~~~~~~~~~~~~~~~~~

There are some scripts to provide you with convenient ways to setup a quick deployment.

.. code-block:: sh

  # Fast deploy on kovan | ropsten | rinkeby | tester | privtest

  cd microraiden/contracts

  # Following two calls are equivalent
  python -m deploy.deploy_testnet  # --owner is web.eth.accounts[0]
  python -m deploy.deploy_testnet \
    --chain kovan \
    --owner `0xf590ee24CbFB67d1ca212e21294f967130909A5a` \
    --challenge-period 500 \
    --token-name CustomToken --token-symbol TKN \
    --supply 10000000 --token-decimals 18 

  # Provide an already deployed, custom token:
  python -m deploy.deploy_testnet --token-address TOKEN_ADDRESS

Apart from the :code:`--owner` argument, above are the default values.
The script provides the following command-line options:

.. click:: deploy.deploy_testnet:main
       :prog: python -m deploy.deploy_testnet
       :show-nested:

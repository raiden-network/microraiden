===========================================
Setup µRaiden Raspberry Pi in local network
===========================================

.. toctree::
  :maxdepth: 2

Prerequisites
==================================

- Install the raspberry pi with the  `RASPBIAN STRETCH WITH DESKTOP <https://www.raspberrypi.org/downloads/raspbian/>`_ OS.

- Set-up the raspberry pi an explanation can be found `here <https://youtu.be/WBlXvGwkZa8>`_ .

- Setup the wifi referring to `this <https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md>`_ official guide.

- Login through ssh client(like putty or moba xterm) on windows or a standard terminal if you are on a linux based system.

.. code ::

  $ ssh pi@192.168.1.105


- We highly recommend using a virtual environment with `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_

``sudo pip install virtualenv virtualenvwrapper``

``export WORKON_HOME=~/Envs``

``mkdir -p $WORKON_HOME``

``source /usr/local/bin/virtualenvwrapper.sh``

``mkvirtualenv -p /usr/bin/python3.5 uRaiden``

- Clone and setup microraiden

``git clone https://github.com/raiden-network/microraiden.git``

``cd microraiden/``

.. code ::

  sudo apt-get install libffi-dev libtool python-dev libssl-dev python-setuptools build-essential automake pkg-config libgmp-dev


``pip install -r requirements.txt``

``python setup.py develop``


Running µRaiden Client and Server
====================================

.. figure:: /diagrams/SetupRasPi.png
   :alt:


As the next step, you are going to setup the raspberry pi as the µRaiden client or the sender and our PC as as the µRaiden proxy server as well as the web3 provider running a geth node synced to Ropsten testnet. Next, you will run the ``echo_server`` and the ``echo_client``  examples from the ``microraiden/examples`` folder, the ``echo_client`` on the raspberry pi and the ``echo_server`` on our PC.

Please make sure that the raspberry pi and your PC are in the same network.

Install the go-ethereum client called **geth** on your PC using the guide  `here <http://github.com/ethereum/go-ethereum/wiki/Installing-Geth>`_


Running geth on the PC
-------------------------------------------
Start geth with these flags(**run this command on PC**)

.. code ::

  geth --testnet --syncmode "fast" --rpc --rpcapi eth,net,web3,personal --rpcaddr 0.0.0.0 --rpcport 8545 --rpccorsdomain "*" --cache 256


The `rpcaddr` as **0.0.0.0** means that a given socket is listening on all the available IP addresses the computer has. This is important so that µRaiden client on the raspberry can use it as a **web3** provider.

Before running both the client or the server make sure that both the sender and receiver addresses have `TKN balances for opening channels <https://docs.google.com/document/d/1cr2yeoqGi0gSbcRjUl8841ZqVuyDf_mRW3Gr2Qw5T10/edit#heading=h.j0rsbka7yn17>`_ .


Running the µRaiden Proxy Server
----------------------------------------


In the ``~/microraiden/microraiden/examples`` folder go to the ``echo_server.py`` and go to the part where we start the server.(These set of actions are performed on **your PC**)

``cd ~/microraiden/microraiden/examples``

.. code :: python

    # Start the app. proxy is a WSGI greenlet, so you must join it properly.
    app.run(debug=True)


Change the `app.run` to include arguments for the `host` and `port`

``app.run(host="192.168.1.104", port=5000, debug=True)``

``192.168.1.104`` This IP could be different your set-up. Include the IP address of the interface on your PC that is connected to the raspberry pi.


.. code ::

 $ python -m  echo_server --private-key ~/.ethereum/testnet/keystore/UTC--2016-07-27T07-40-38.092883212Z--9d80d905bc1e106d5bd0637c12b893c5ab60cb41
  Enter the private key password:
  INFO:filelock:Lock 139916998263696 acquired on ~/.config/microraiden/echo_server.db.lock
  INFO:blockchain:starting blockchain polling (interval 2s)


Running the µRaiden client on the raspberry pi
-----------------------------------------------

Navigate to the cloned microraiden repository and modify the following files on the **raspberry pi**.

``cd ~/microraiden/microraiden``

1. In the ``microraiden/constants.py`` file change the  **WEB3_PROVIDER_DEFAULT** value to ``"http://192.168.1.104:8545"``  where  ``192.168.1.104``  is the IP address of the PC where we started the geth node and the µRaiden ``echo_server``.

``sudo nano microraiden/constants.py``

2. In the ``microraiden/examples/echo_client.py``  change ``endpoint_url`` parameter of the `run` function
   definition which looks like this

.. code :: python

  def run(
        private_key: str,
        password_path: str,
        resource: str,
        channel_manager_address: str = None,
        web3: Web3 = None,
        retry_interval: float = 5,
        endpoint_url: str = 'http://localhost:5000'
  ):

to the interface of the PC like this ``endpoint_url: str = 'http://192.168.1.104:5000'``. This enables the raspberry to make a request to the server.

``sudo nano microraiden/examples/echo_client.py``

Now we run the `echo_client.py` like this

.. code ::

   (uRaiden) pi@raspberrypi:~/microraiden/microraiden $ python -m  microraiden.examples.echo_client --private-key              ~/.ethereum/testnet/keystore/UTC--2018-02-12T08-35-34.437506909Z--9a7d8c3116258c1f50f3c8ac67d120af58a46ceb --resource        /echofix/hello
   Enter the private key password:
   INFO:microraiden.client.client:Creating channel to 0x9d80D905bc1E106d5bd0637c12B893c5Ab60CB41 with an initial deposit of    50 @2684938
   WARNING:microraiden.client.session:Newly created channel does not have enough confirmations yet. Retrying in 5 seconds.
   INFO:root:Got the resource /echofix/hello type=text/html; charset=utf-8:
   hello

You should get an output like above.The server should also give an output like this showing the requested resource

.. code ::

   INFO:channel_manager:unconfirmed channel event received (sender 0x9A7d8c3116258C1F50f3c8ac67d120af58a46CeB, block_number 2684940)
   192.168.1.109 - - [2018-02-20 00:41:05] "GET //echofix/hello HTTP/1.1" 402 391 0.010679
   INFO:channel_manager:new channel opened (sender 0x9A7d8c3116258C1F50f3c8ac67d120af58a46CeB, block number 2684940)
   INFO:__main__:Resource requested: http://192.168.1.104:5000/echofix/hello with param "hello"
   192.168.1.109 - - [2018-02-20 00:41:10] "GET //echofix/hello HTTP/1.1" 200 120 0.060261

Through this example we hope developers can develop their own machine to machine clients and their respective server to use microraiden for micropayments according to their respective use cases, using these resources.

1. microraiden **Session** Library (source microraiden/microraiden/client/session.py)
2. microraiden **Requests** Library (source microraiden/microraiden/requests/__init__.py)
3. microraiden **Client** Library (microraiden/microraiden/client/client.py)

Troubleshooting
==============================

**Failed building wheel for secp256k1**.

  If you encounter this problem its mostly your openssl not being compatible with the `libsecp256k1 <https://github.com/bitcoin-core/secp256k1>`_ library. `secp256k1 <https://github.com/ludbb/secp256k1-py>`_ is the python binding for this library.

To check whether libsecp256k1 is installed do the following:

.. code ::

  (uRaiden) pi@raspberrypi:~ $ apt list --installed *secp256k1*
  Listing... Done
  (uRaiden) pi@raspberrypi:~ $ apt list  *secp256k1*
  Listing... Done
  libsecp256k1-0/stable 0.1~20161228-1 armhf
  libsecp256k1-dev/stable 0.1~20161228-1 armhf

The ``installed`` option tells us whether the package is installed. Since we have none it does not print anything. Later we list the packages which exists in raspbian repository of packages. We install both the packages.

``sudo apt-get install libsecp256k1-0 libsecp256k1-dev``

After this we go to the releases page of
`secp256k1 <https://github.com/ludbb/secp256k1-py/releases>`_ and download the tar.gz of `0.13.2.4` (version as of writing of this tutorial) like this.

``wget https://github.com/ludbb/secp256k1-py/archive/0.13.2.4.tar.gz``

From the current folder we install tar.gz package of *secp256k1* like this.

``pip install 0.13.2.4.tar.gz``

After this again install **requirements.txt**

``pip install -r requirements.txt``

For Transferring file from your machine to the Raspberry pi refer to this documentation

https://www.raspberrypi.org/documentation/remote-access/ssh/sftp.md

You could download and use filezilla.



References
===========================
- http://digitalatomindustry.com/install-ethereum-blockchain-on-raspberry-pi/
- http://raspnode.com/diyEthereumGeth.html
- https://golang.org/dl/
- https://geth.ethereum.org/downloads/
- https://ethereum.stackexchange.com/questions/31610/how-to-install-geth-on-rpi-3b
- https://owocki.com/install-ethereum-geth-raspberry-pi-b/
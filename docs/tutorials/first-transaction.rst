Your first microtransaction
=============================

In order to get you started, we created an example application for you, that receives micropayments and some 
parameter over a http-request - and simply echos this parameter when the micropayment was valid.
Please follow the instructions
:doc:`here <../dev-setup>`
to set up geth and install microraiden.

Starting the µRaiden Receiver
-------------------------------

From the root directory of microraiden, start:

.. code:: sh

    python microraiden/examples/echo_server.py --private-key microraiden/examples/pk_tut.txt

*Note: the file pk_tut.txt should contain your private key as exported in the Blockchain Setup guide by MetaMask.*

Starting the µRaiden Sender
----------------------------

To actually start the request for resource /hello, we will fire up the µRaiden client with the prefunded account.

While the Receiver is still running (in another terminal window for example), execute this command from the µRaiden root folder:

.. code:: sh

   python microraiden/examples/echo_client.py --private-key microraiden/examples/pk_tut.txt --resource /echofix/hello

After some seconds, you should get the output

.. code:: sh

   INFO:root:Got the resource /echofix/hello type=text/html; charset=utf-8:
   hello

This means: 
 - a channel has been created
 - a deposit of 50 aTKN has been escrowed 
 - a micropayment of 1 aTKN has been transferred to the receiver
 - the receiver returned the requested resource (the “hello” parameter in this simple case) for this payment

Congratulations, you just performed your first micropayment!


Tutorials
=======================================

Before getting started with the tutorials, 
please make sure that you have µRaiden installed properly for development.

To do so, either simply run these commands in a terminal, or follow our more detailed :doc:`guide <../pyserver/installation>`.

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate
    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden
    make pip-install-dev

If you don't know how to properly set up everything that interacts with 
the Ethereum blockchain, you should have a look at the :doc:`blockchain setup tutorial <blockchain>`.
There you learn how to get a Ethereum node running and how to use MetaMask in order to aquire some
neccessary µRaiden-tokens on the live Ethereum test-network.

For simply getting started and testing out if everything in your setup works,
you can execute :doc:`your first microtransaction <first-transaction>`

In the :doc:`proxy tutorial <proxy-tutorial>` you learn how to write some custom classes 
for the server side of µRaiden, in order to serve custom content. This is a good starting 
point if you want to integrate µRaiden into your application.


.. toctree::
   :maxdepth: 1

   blockchain     
   first-transaction
   proxy-tutorial


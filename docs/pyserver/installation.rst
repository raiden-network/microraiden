Installation
---------------

Using ``virtualenv``
~~~~~~~~~~~~~~~~~~~~

Run the following commands from the repository root directory.

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate
    pip install -e microraiden

Using microraiden in pip's *editable* mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because of ``gevent`` you will need to install microraiden's
requirements first.

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate
    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden/microraiden
    pip install -r requirements-dev.txt
    pip install -e .

Using a global ``pip3`` installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    sudo pip3 install -e microraiden

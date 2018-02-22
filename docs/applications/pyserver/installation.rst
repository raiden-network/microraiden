Installation
---------------

It is required that you have python's `pip` installed.
You probably already have this dependency, but if not,
please visit `the official pip documentation <https://pip.pypa.io/en/stable/installing/>`_ 
and install pip before you proceed.

Using ``virtualenv``
~~~~~~~~~~~~~~~~~~~~

It is recommended to use a virtual environment 
to separate your global python application from 
the environment (all the dependency-packages) µRaiden
likes to run in.
This will fetch the latest release of µRaiden
directly from the Python package index and install it:

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate
    pip install microraiden

*editable* development installation 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you want to develop on the µRaiden codebase,
it is best to install it in pip's *editable* mode.
This way, you can edit the source code directly and 
never worry about re-installing µRaiden - the linked 
application always reflects the changes you made.

To install µRaiden for development, simply run:

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate
    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden

    make pip-install-dev

If you don't like our make script install, you can also run
the commands manually like so:

.. code:: bash
    pip install -r requirements-dev.txt
    pip install -e .

Using a global ``pip3`` installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This method is not recommended, as it 
can interfere with your global python installation.
If you absolutely must, it still works though:

.. code:: bash

    sudo pip3 install microraiden

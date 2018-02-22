Development setup
=======================================

Requirements
---------------
It is required that you have python’s pip, python3.5 and git installed.
You can visit `the official pip documentation <https://pip.pypa.io/en/stable/installing/>`_ and install pip before you proceed.

Using ``virtualenv``
---------------
It is recommended to use a virtual environment to separate your global python application from the environment
(all the dependency-packages) µRaiden likes to run in:

.. code:: bash

    virtualenv -p python3 env
    . env/bin/activate

uRaiden dev-installation
---------------

When you want to develop on the µRaiden codebase, it is best to install it in pip’s editable mode.
This way, you can edit the source code directly and never worry about re-installing µRaiden -
the linked application always reflects the changes you made.
To install µRaiden for development, download the repository and run the makefile:

.. code:: bash

    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden
    make pip-install-dev


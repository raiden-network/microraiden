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

    python3 -m venv env
    . env/bin/activate

 A short check of the location of your python version should show the :code:`./env/bin/python` binary.

.. code:: bash

    which python

To switch back to your usual python executable, simply deactivate the `venv`:

.. code:: bash

    deativate 

There are more sophisticated tools to keep track of your virtualenvs and python installations.
For example, check out `pyenv <https://github.com/pyenv/pyenv>`_ in combination with `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_.

µRaiden installation for development
--------------------------------------

When you want to develop on the µRaiden codebase, it is best to install it in pip’s editable mode.
This way, you can edit the source code directly and never worry about re-installing µRaiden -
the linked application always reflects the changes you made.
To install µRaiden for development, download the repository and run our simplified install script with:

.. code:: bash

    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden
    make pip-install-dev


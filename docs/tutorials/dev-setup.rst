Development setup
=================

Requirements
------------
It is required that you have :code:`pip`, :code:`python` (version 3.5 or greater) and :code:`git` installed.

- To install pip, see the official `documentation <https://pip.pypa.io/en/stable/installing/>`_
- To install Python `download the latest version <https://www.python.org/downloads/>`_ 
- If you don't have git, `download it here <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_

Python environment setup
------------------------
In general, it is recommended to use a virtual environment to separate your global python application from the environment
(all the dependency-packages) µRaiden likes to run in:

.. code:: bash

    python3 -m venv env
    . env/bin/activate

A short check of the location of your python version should show the :code:`./env/bin/python` binary.

.. code:: bash

    which python

To switch back to your usual python executable, simply deactivate the `venv`:

.. code:: bash

    deactivate

There are more sophisticated tools to keep track of your virtualenvs and python installations.
For example, check out `pyenv <https://github.com/pyenv/pyenv>`_ in combination with `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_.

.. _dev-installation:

µRaiden installation for development
------------------------------------

When you want to develop on the µRaiden codebase, it is best to install it in pip’s editable mode.
This way, you can edit the source code directly and never worry about reinstalling µRaiden -
the linked application always reflects the changes you made.
To install µRaiden for development, download the repository and run our install script with:

.. code:: bash

    git clone git@github.com:raiden-network/microraiden.git
    cd microraiden
    make pip-install-dev

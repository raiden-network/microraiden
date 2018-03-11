Usage
=====

There are several examples that demonstrate how to serve custom content.
To try them, run one of the following commands from a Python environment containing a successful µRaiden installation:

.. code:: bash

    python3 -m microraiden.examples.demo_proxy --private-key <path_to_private_key_file> start

or

.. code:: bash

    python3 -m microraiden.examples.wikipaydia --private-key <path_to_private_key_file> --private-key-password-file <path_to_password_file> start

By default, the web server listens on ``0.0.0.0:5000``. The private key
file should be in the JSON format produced by Geth/Parity and must be
readable and writable only by the owner to be accepted (``-rw-------``).

A :code:`--private-key-password-file` option can be specified, containing
the password for the private key in the first line of the file. If it's
not provided, the password will be prompted interactively.
With the above commands, an Ethereum nodes RPC interface is expected to respond on http://localhost:8545.

If you want to specify a different endpoint for this, use the :code:`--rpc-provider` commandline option.

For more command line options, have a look :doc:`here <cmdline>`.
To setup :code:`geth`, please refer to our :doc:`Blockchain setup tutorial </tutorials/blockchain>`.

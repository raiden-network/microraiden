Execution
==========

There are several examples that demonstrate how to serve custom content.
To try them, run one of the following commands from the ``microraiden``
directory:

.. code:: bash

    python3 -m microraiden.examples.demo_proxy --private-key <private_key_file> start

or

.. code:: bash

    python3 -m microraiden.examples.wikipaydia --private-key <private_key_file> --private-key-password-file <password_file> start

By default, the web server listens on ``0.0.0.0:5000``. The private key
file should be in the JSON format produced by Geth/Parity and must be
readable and writable only by the owner to be accepted (``-rw-------``).
A ``--private-key-password-file`` option can be specified, containing
the password for the private key in the first line of the file. If it's
not provided, the password will be prompted interactively. An Ethereum
node RPC interface is expected to respond on http://localhost:8545.
Alternatively, you can use `Infura
infrastructure <https://infura.io/>`__ as a RPC provider.

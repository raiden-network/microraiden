Usage
---------


The µRaiden client can be used as a standalone library, to make machine-to-machine payments easily available.
After installation, import the following class:

.. code:: python

    from microraiden import Client

    client = Client('<hex-encoded private key>')

Alternatively you can specify a path to a JSON private key, optionally
specifying a file containing the password. If it's not provided, it'll
be prompted interactively.

.. code:: python

    client = Client(key_path='<path to private key file>', key_password_file='<path to password file>')

This client object allows interaction with the blockchain and
offline-signing of transactions and Raiden balance proofs.

An example lifecycle of a ``Client`` object could look like this:

.. code:: python

    from microraiden import Client

    receiver = '0xb6b79519c91edbb5a0fc95f190741ad0c4b1bb4d'
    privkey = '0x55e58f57ec2177ea681ee461c6d2740060fd03109036e7e6b26dcf0d16a28169'

    # 'with' statement to cleanly release the client's file lock in the end.
    with Client(privkey) as client:

        channel = client.get_suitable_channel(receiver, 10)
        channel.create_transfer(3)
        channel.create_transfer(4)

        print(
            'Current balance proof:\n'
            'From: {}\n'
            'To: {}\n'
            'Channel opened at block: #{}\n'  # used to uniquely identify this channel
            'Balance: {}\n'                   # total: 7
            'Signature: {}\n'                 # valid signature for a balance of 7 on this channel
            .format(
                channel.sender, channel.receiver, channel.block, channel.balance, channel.balance_sig
            )
        )

        channel.topup(5)                      # total deposit: 15

        channel.create_transfer(5)            # total balance: 12

        channel.close()

        # Wait for settlement period to end.

        channel.settle()

        # Instead of requesting a close and waiting for the settlement period to end, you can also perform
        # a cooperative close, provided that you have a receiver-signed balance proof that matches your
        # current channel balance.

        channel.close_cooperatively(closing_sig)

The values required for a valid balance proof required by the receiver
end are printed above. Make sure to let them know.

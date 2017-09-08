# Raiden Micropayment Service

## Installation

### Using `virtualenv`

Run the following commands from the repository root directory.

```bash
virtualenv -p python3 env
. env/bin/activate
pip install -e microraiden
```

### Using a global `pip3` installation

```bash
sudo pip3 install -e microraiden
```

## Execution

### HTTP Proxy
There are several examples that demonstrate how to serve a custom content.
By default, web server listens on 0.0.0.0:5000, and Ethereum node RPC interface is expected to respond on http://localhost:8545.
```bash
python3 -m microraiden.examples.demo_proxy start
```
or
```bash
python3 -m microraiden.examples.wikipaydia start
```

### M2M Client
```bash
python3 -m microraiden.examples.m2m_client --key-path <path to private key file>
```

The private key file should contain a valid (and preferably sufficiently funded) private key in hex format, with or without a leading `0x` prefix.

## Library use

### Client
The Raiden client backend used by the M2M sample client can be used as a standalone library. After installation, import the following class:
```python
from microraiden import Client

client = Client('<hex-encoded private key>')
```

Alternatively you can specify a path to a file containing the private key, again in a hex-encoded format, with or without a leading `0x` prefix.
```python
client = Client(key_path='<path to private key file>'
```

This client object allows interaction with the blockchain and offline-signing of transactions and Raiden balance proofs.

An example lifecycle of a `Client` object could look like this:

```python
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
```

The values required for a valid balance proof required by the receiver end are printed above. Make sure to let them know.

# Raiden Micropayment Service

## Installation

### Using `virtualenv`

Run the following commands from the repository root directory.

```bash
virtualenv -p python3 env
. env/bin/activate
pip install -e raiden_mps
```

### Using a global `pip3` installation

```bash
sudo pip3 install -e raiden_mps
```

## Execution

### HTTP Proxy
```bash
python3 -m raiden_mps.proxy 
```

### M2M Client
```bash
python3 -m raiden_mps.client --key-path <path to private key file>
```

The private key file should contain a valid (and preferably sufficiently funded) private key in hex format, without a leading `0x` prefix.

## Library use

### RMP Client
The Raiden client backend used by the M2M sample client can be used as a standalone library. After installation, import the following class:
```python
from raiden_mps.client.rmp_client import RMPClient

client = RMPClient('<hex-encoded private key (without leading 0x)>')
```

Alternatively you can specify a path to a file containing the private key, again in a hex-encoded format, without a leading `0x` prefix.
```python
client = RMPClient(key_path='<path to private key file>'
```

This client object allows interaction with the blockchain and offline-signing of transactions and Raiden balance proofs.

An example lifecycle of an `RMPClient` object could look like this:

```python
receiver = '0xb6b79519c91edbb5a0fc95f190741ad0c4b1bb4d'
client = RMPClient('55e58f57ec2177ea681ee461c6d2740060fd03109036e7e6b26dcf0d16a28169')

channel = client.open_channel(receiver, 10)
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
```

The values required for a valid balance proof required by the receiver end are printed above. Make sure to let them know.

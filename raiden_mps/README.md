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
python3 -m raiden_mps.client --key-path <path_to_hex_encoded_private_key>
```

## Library use

### RMP Client
The Raiden client backend used by the M2M sample client can be used as a standalone library. After installation import the following class:
```python
from raiden_mps.client.rmp_client import RMPClient
```

This class allows interaction with the blockchain and offline-signing of transactions and Raiden balance proofs.


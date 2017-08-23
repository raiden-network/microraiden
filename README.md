# MicroRaiden

Off-chain, cheap, scalable, low-latency micropayment solution.

## Quick Start

 * install and run the Proxy component (more details [here](/raiden_mps/README.md)):

```

cd raiden-micropayment-service
virtualenv -p python3 env
. env/bin/activate
pip install -e raiden_mps
cd raiden_mps
python3 -m raiden_mps.proxy

```

 * Go to the paywalled resource pages:
    - http://localhost:5000/doggo.jpg
    - http://localhost:5000/kitten.jpg
    - http://localhost:5000/teapot.jpg
    - http://localhost:5000/test.txt


## How To

You can use the configuration for the above default example for creating your own payment channel service.

 * MicroRaiden Paywall Tutorial:
   - Proxy: [/docs/proxy-tutorial.md](/docs/proxy-tutorial.md)
   - Web Interface: [/raiden_mps/raiden_mps/webui/README.md](/raiden_mps/raiden_mps/webui/README.md)
 * Various paywall [examples](/raiden_mps/raiden_mps/examples)


## Development Documentation

 * Components Overview: [/docs/dev_overview.md](/docs/dev_overview.md)
 * MicroRaiden Service Setup: [/raiden_mps/README.md](/raiden_mps/README.md)
 * Smart Contracts Setup: [/contracts/README.md](/contracts/README.md)

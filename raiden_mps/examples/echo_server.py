"""
This is dummy code showing how the minimal app could look like.
In his case we don't use a proxy, but directly a server
"""
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy
from raiden_mps.test.utils import BlockchainMock
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS
from raiden_mps.proxy.content import (
    PaywalledContent
)

if __name__ == '__main__':
    config = {
        "contract_address": CHANNEL_MANAGER_ADDRESS,
        "receiver_address": '0x004B52c58863C903Ab012537247b963C557929E8',
        "private_key": 'b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
    }
    blockchain = BlockchainMock(None, None)
    app = PaywalledProxy(blockchain, config)
    # resource with a fixed price 1
    app.add_content(PaywalledContent(
                    "echofix\/[0-9]+", 1, lambda request:
                    (int(request.split("/")[1]), 200)))
    # resource with a price based on second param
    app.add_content(PaywalledContent(
                    "echodyn\/[0-9]+",
                    lambda request: int(request.split("/")[1]),
                    lambda request: (int(request.split("/")[1]), 200)))
    app.run(debug=True)

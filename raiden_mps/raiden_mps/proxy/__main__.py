import click
import os
import sys
#
# Flask restarts itself when a file changes, but this restart
#  does not have PYTHONPATH set properly if you start the
#  app with python -m raiden_mps.
#
if __package__ is None:
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    sys.path.insert(0, path + "/../")

from raiden_mps.config import CHANNEL_MANAGER_ADDRESS
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy
from raiden_mps.proxy.content import (
    PaywalledFile,
    PaywalledContent,
    PaywalledProxyUrl
)
from raiden_mps.test.utils import BlockchainMock
from raiden_mps.channel_manager import Blockchain


@click.command()
@click.option('--mock-blockchain', default=True, is_flag=True,
              help='Use mocked blockchain instance')
@click.option(
    '--channel-manager-address',
    default=CHANNEL_MANAGER_ADDRESS,
    help='Ethereum address of the channel manager contract.'
)
def main(
    channel_manager_address,
    mock_blockchain
):
    config = {
        "contract_address": channel_manager_address,
        "receiver_address": '0x004B52c58863C903Ab012537247b963C557929E8',
        "private_key": 'b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
    }
    if mock_blockchain:
        blockchain = BlockchainMock(None, None)
    else:
        blockchain = Blockchain(None, None)
    app = PaywalledProxy(blockchain, config)
    app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
    app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
    app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
    app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
    app.add_content(PaywalledProxyUrl("p\/.*", 1))
    app.run(debug=True)


if __name__ == '__main__':
    main()

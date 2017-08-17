import click
import os
import sys
from ethereum.utils import encode_hex, privtoaddr
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


@click.command()
@click.option(
    '--channel-manager-address',
    default=CHANNEL_MANAGER_ADDRESS,
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--state-file',
    default=None,
    help='State file of the proxy'
)
@click.option(
    '--private-key',
    default='b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946',
    help='Private key of the proxy'
)
@click.option(
    '--paywall-info',
    default='raiden_mps/data/html/',
    help='Directory where the paywall info is stored. '
         'The directory shoud contain a index.html file with the payment info/webapp. '
         'Content of the directory (js files, images..) is available on the "js/" endpoint.'
)
def main(
    channel_manager_address,
    state_file,
    private_key,
    paywall_info
):
    if os.path.isfile(private_key):
        with open(private_key) as keyfile:
            private_key = keyfile.readline()[:-1]

    receiver_address = '0x' + encode_hex(privtoaddr(private_key)).decode()

    if not state_file:
        state_file_name = "%s_%s.pkl" % (channel_manager_address, receiver_address)
        state_file = os.path.join(os.path.expanduser('~'), '.raiden') + "/" + state_file_name
    app = PaywalledProxy(channel_manager_address,
                         private_key,
                         state_file,
                         paywall_html_dir=paywall_info)
    app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
    app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
    app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
    app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
    app.add_content(PaywalledProxyUrl("p\/.*", 1))
    app.run(debug=True)
    app.join()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()

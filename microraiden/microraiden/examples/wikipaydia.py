import click
import os
import sys

if __package__ is None:
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    sys.path.insert(0, path + "/../")

from microraiden.make_helpers import make_paywalled_proxy
from microraiden import config
from microraiden.crypto import privkey_to_addr
from microraiden.proxy.content import (
    PaywalledProxyUrl
)


@click.command()
@click.option(
    '--channel-manager-address',
    default=None,
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--private-key',
    default='b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946',
    help='Private key of the proxy'
)
@click.option(
    '--host',
    default='localhost',
    help='Address of the proxy'
)
@click.option(
    '--port',
    default=5000,
    help='Port of the proxy'
)
@click.option(
    '--state-file',
    default=None,
    help='Port of the proxy'
)
@click.option(
    '--paywall-info',
    default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../webui')),
    help='Directory where the paywall info is stored. '
         'The directory shoud contain a index.html file with the payment info/webapp. '
         'Content of the directory (js files, images..) is available on the "js/" endpoint.'
)
def main(
    channel_manager_address,
    private_key,
    paywall_info,
    state_file,
    host,
    port
):
    if os.path.isfile(private_key):
        with open(private_key) as keyfile:
            private_key = keyfile.readline()[:-1]

    channel_manager_address = channel_manager_address or config.CHANNEL_MANAGER_ADDRESS
    receiver_address = privkey_to_addr(private_key)
    if not state_file:
        state_file_name = "%s_%s.pkl" % (channel_manager_address[:10], receiver_address[:10])
        app_dir = click.get_app_dir('microraiden')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        state_file = os.path.join(app_dir, state_file_name)

    config.paywall_html_dir = paywall_info
    app = make_paywalled_proxy(private_key, state_file)

    app.add_content(PaywalledProxyUrl(".*", 1, "http://en.wikipedia.org/", [r"wiki/.*"]))
    app.run(host=host, port=port, debug=True)
    app.join()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()

import click
import os
import sys
#
# Flask restarts itself when a file changes, but this restart
#  does not have PYTHONPATH set properly if you start the
#  app with python -m microraiden.
#
from microraiden.crypto import privkey_to_addr
from flask import make_response
import logging

log = logging.getLogger(__name__)


if __package__ is None:
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    sys.path.insert(0, path + "/../")

import microraiden.utils as utils
from microraiden.make_helpers import make_paywalled_proxy
from microraiden import config
from microraiden.proxy.content import (
    PaywalledFile,
    PaywalledContent
)
from microraiden.channel_manager import StateFileLocked, InsecureStateFile


def get_doggo(_):
    doggo_str = """
         |\_/|
         | @ @   Woof!
         |   <>              _
         |  _/\------____ ((| |))
         |               `--' |
     ____|_       ___|   |___.'
    /_/_____/____/_______|
    """
    headers = {"Content-type": 'text/ascii'}
    return make_response(doggo_str, 200, headers)


@click.command()
@click.option(
    '--channel-manager-address',
    default=None,
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
    '--ssl-cert',
    default=None,
    help='Cerfificate of the server (cert.pem or similar)'
)
@click.option(
    '--ssl-key',
    default=None,
    help='SSL key of the server (key.pem or similar)'
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
    ssl_key,
    ssl_cert,
    state_file,
    private_key,
    paywall_info
):
    if os.path.isfile(private_key):
        if utils.is_file_rwxu_only(private_key) is False:
            log.fatal("Private key file %s must be readable only by its owner." % (private_key))
            sys.exit(1)
        with open(private_key) as keyfile:
            private_key = keyfile.readline()[:-1]

    receiver_address = privkey_to_addr(private_key)
    channel_manager_address = channel_manager_address or config.CHANNEL_MANAGER_ADDRESS

    if not state_file:
        state_file_name = "%s_%s.pkl" % (channel_manager_address[:10], receiver_address[:10])
        app_dir = click.get_app_dir('microraiden')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        state_file = os.path.join(app_dir, state_file_name)

    config.paywall_html_dir = paywall_info
    try:
        app = make_paywalled_proxy(private_key, state_file)
    except StateFileLocked as ex:
        log.fatal('Another uRaiden process is already running (%s)!' % str(ex))
        sys.exit(1)
    except InsecureStateFile as ex:
        msg = ('The permission bits of the state file (%s) are set incorrectly (others can '
               'read or write) or you are not the owner. For reasons of security, '
               'startup is aborted.' % state_file)
        log.fatal(msg)
        sys.exit(1)

    app.add_content(PaywalledContent("kitten.jpg", 1, lambda _: ("HI I AM A KITTEN", 200)))
    app.add_content(PaywalledContent("doggo.jpg", 2, lambda _: ("HI I AM A DOGGO", 200)))
    app.add_content(PaywalledContent("doggo.txt", 2, get_doggo))
    app.add_content(PaywalledContent("teapot.jpg", 3, lambda _: ("HI I AM A TEAPOT", 418)))
    app.add_content(PaywalledFile("test.txt", 10, "/tmp/test.txt"))
    app.run(debug=True, ssl_context=(ssl_key, ssl_cert))
    app.join()


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()

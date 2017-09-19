import click
import os
import sys
#
# Flask restarts itself when a file changes, but this restart
#  does not have PYTHONPATH set properly if you start the
#  app with python -m microraiden.
#
from microraiden.crypto import privkey_to_addr
import logging
import requests

log = logging.getLogger(__name__)


if __package__ is None:
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    sys.path.insert(0, path + "/../")

from eth_utils import decode_hex, is_hex
from web3 import HTTPProvider, Web3
import microraiden.utils as utils
from microraiden.make_helpers import make_paywalled_proxy
from microraiden import config
from microraiden.exceptions import StateFileLocked, InsecureStateFile, NetworkIdMismatch
from microraiden.proxy.paywalled_proxy import PaywalledProxy

pass_app = click.make_pass_decorator(PaywalledProxy)


@click.group()
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
    help='Path to private key file of the proxy',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--ssl-cert',
    default=None,
    help='Cerfificate of the server (cert.pem or similar)'
)
@click.option(
    '--rpc-provider',
    default='http://localhost:8545',
    help='Address of the Ethereum RPC provider'
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
@click.pass_context
def main(
    ctx,
    channel_manager_address,
    ssl_key,
    ssl_cert,
    state_file,
    private_key,
    paywall_info,
    rpc_provider,
):
    if private_key is None:
        log.fatal("No private key provided")
        sys.exit(1)
    if utils.check_permission_safety(private_key) is False:
        log.fatal("Private key file %s must be readable only by its owner." % (private_key))
        sys.exit(1)
    with open(private_key) as keyfile:
        private_key = keyfile.readline()[:-1]
    if not is_hex(private_key) or len(decode_hex(private_key)) != 32:
        log.fatal("Private key must be specified as 32 hex encoded bytes")
        sys.exit(1)

    receiver_address = privkey_to_addr(private_key)
    channel_manager_address = channel_manager_address or config.CHANNEL_MANAGER_ADDRESS

    if not state_file:
        state_file_name = "%s_%s.json" % (channel_manager_address[:10], receiver_address[:10])
        app_dir = click.get_app_dir('microraiden')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        state_file = os.path.join(app_dir, state_file_name)

    config.paywall_html_dir = paywall_info
    web3 = Web3(HTTPProvider(rpc_provider, request_kwargs={'timeout': 60}))
    try:
        app = make_paywalled_proxy(private_key, state_file, web3=web3)
    except StateFileLocked as ex:
        log.fatal('Another uRaiden process is already running (%s)!' % str(ex))
        sys.exit(1)
    except InsecureStateFile as ex:
        msg = ('The permission bits of the state file (%s) are set incorrectly (others can '
               'read or write) or you are not the owner. For reasons of security, '
               'startup is aborted.' % state_file)
        log.fatal(msg)
        sys.exit(1)
    except NetworkIdMismatch as ex:
        log.fatal(str(ex))
        sys.exit(1)
    except requests.exceptions.ConnectionError as ex:
        log.fatal("Ethereum node refused connection: %s" % str(ex))
        sys.exit(1)
    ctx.obj = app

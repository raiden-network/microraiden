"""
This is dummy code showing how the minimal app could look like.
"""
import click
import re
from microraiden import Client
from microraiden import DefaultHTTPClient
import logging
import requests


@click.command()
@click.option(
    '--key-path',
    required=True,
    help='Path to private key file.',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--key-password-path',
    default=None,
    help='Path to file containing password for private key.',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option('--resource', required=True, help='Get this resource.')
def run(key_path, key_password_path, resource):
    # create the client
    with Client(key_path=key_path, key_password_path=key_password_path) as client:
        m2mclient = DefaultHTTPClient(
            client,
            'localhost',
            5000
        )

        # Get the resource. If payment is required, client will attempt to create
        # a channel or will use existing one.
        status, headers, body = m2mclient.run(resource)
        if status == requests.codes.OK:
            if re.match('^text\/', headers['Content-Type']):
                logging.info("got the resource %s type=%s\n%s" % (
                    resource,
                    headers.get('Content-Type', '???'),
                    body))
            else:
                logging.info("got the resource %s type=%s" % (
                    resource,
                    headers.get('Content-Type', '???')))
        else:
            logging.error("error getting the resource. code=%d body=%s" %
                          (status, body.decode().strip()))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()

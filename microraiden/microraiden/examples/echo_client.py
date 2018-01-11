"""
This is dummy code showing how the minimal app could look like.
"""
import click
import re

from web3 import Web3

from microraiden import Session
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
def main(
        key_path: str,
        key_password_path: str,
        resource: str
):
    run(key_path, key_password_path, resource)


def run(
        key_path: str,
        key_password_path: str,
        resource: str,
        channel_manager_address: str = None,
        web3: Web3 = None,
        retry_interval: float = 5,
        endpoint_url: str = 'http://localhost:5000'
):
    # Create the client session.
    session = Session(
        endpoint_url=endpoint_url,
        private_key=key_path,
        key_password_path=key_password_path,
        channel_manager_address=channel_manager_address,
        web3=web3,
        retry_interval=retry_interval
    )
    # Get the resource. If payment is required, client will attempt to create
    # a channel or will use existing one.
    response = session.get('{}/{}'.format(endpoint_url, resource))

    if response.status_code == requests.codes.OK:
        if re.match('^text/', response.headers['Content-Type']):
            logging.info(
                "Got the resource {} type={}:\n{}".format(
                    resource,
                    response.headers.get('Content-Type', '???'),
                    response.text
                )
            )
        else:
            logging.info(
                "Got the resource {} type={} (not echoed)".format(
                    resource,
                    response.headers.get('Content-Type', '???')
                )
            )
    else:
        logging.error(
            "Error getting the resource. Code={} body={}".format(
                response.status_code,
                response.text
            )
        )
    return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

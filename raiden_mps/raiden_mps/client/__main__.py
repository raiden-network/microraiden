#!/usr/bin/env python3

import click
import logging

from raiden_mps.client.rmp_client import RMPClient
from raiden_mps.client.m2m_client import M2MClient
from ethereum.utils import encode_hex


@click.command()
@click.option('--api-endpoint', default='localhost', help='Address of the HTTP API server.')
@click.option('--api-port', default=5000)
@click.option('--datadir', help='Raiden data directory.')
@click.option('--rpc-endpoint', help='Address of the Ethereum RPC server.')
@click.option('--rpc-port', help='Ethereum RPC port.')
@click.option('--key-path', help='Path to private key file.')
@click.option(
    '--channel-manager-address',
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--contract-abi-path',
    help='Path to a file containing the ABIs for the token and channel manager.'
)
@click.option(
    '--token-address',
    help='Ethereum address of the token contract.'
)
def run(
        api_endpoint,
        api_port,
        **kwargs
):
    logging.basicConfig(level=logging.INFO)
    kwargs = {key: value for key, value in kwargs.items() if value}
    rmp_client = RMPClient(**kwargs)
    client = M2MClient(
        rmp_client,
        api_endpoint,
        api_port
    )

    resource = 'doggo.jpg'
    client.request_resource(resource)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    run()

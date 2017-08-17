#!/usr/bin/env python3

import logging

import click
from raiden_mps.client.channel import Channel
from raiden_mps.client.rmp_client import RMPClient
from raiden_mps.client.m2m_client import M2MClient


@click.command()
@click.option('--api-endpoint', default='localhost', help='Address of the HTTP API server.')
@click.option('--api-port', default=5000)
@click.option('--datadir', help='Raiden data directory.')
@click.option('--rpc-endpoint', help='Address of the Ethereum RPC server.')
@click.option('--rpc-port', help='Ethereum RPC port.')
@click.option('--key-path', required=True, help='Path to private key file.')
@click.option('--close-channels', default=False, is_flag=True, type=bool,
              help='Close all open channels before exiting.')
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
def run(api_endpoint, api_port, **kwargs):
    logging.basicConfig(level=logging.INFO)
    exclude_kwargs = {'close_channels'}
    kwargs_client = {
        key: value for key, value in kwargs.items() if value and key not in exclude_kwargs
    }
    rmp_client = RMPClient(**kwargs_client)

    client = M2MClient(
        rmp_client,
        api_endpoint,
        api_port
    )

    resource = 'doggo.jpg'
    client.request_resource(resource)

    if kwargs['close_channels'] is True:
        for channel in rmp_client.channels:
            if channel.state == Channel.State.open:
                channel.close_channel()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    run()

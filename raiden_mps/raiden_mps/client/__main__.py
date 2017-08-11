#!/usr/bin/env python3

import click
import os
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
@click.option('--dry-run', default=False, is_flag=True, help='Create and sign transactions without sending them.')
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
    kwargs = {key: value for key, value in kwargs.items() if value}
    rmp_client = RMPClient(**kwargs)
    client = M2MClient(
        rmp_client,
        api_endpoint,
        api_port
    )

    resource = 'doggo.jpg'
    client.request_resource(resource)

    # open_channels = [channel for channel in rmp_client.channels if channel.state.name == 'open']
    # channel = open_channels[0]
    # channel = rmp_client.open_channel('0x003573995FAd11dF98746D286cFE6d87be3d508b', 5)
    # rmp_client.close_channel(channel)
    # rmp_client.create_transfer(channel, 1)
    # print('Balance signature: {}'.format(encode_hex(channel.balance_sig)))

    # settling_channels = [channel for channel in rmp_client.channels if channel.state.name == 'settling']
    # for channel in settling_channels:
    #     rmp_client.settle_channel(channel)
    # for channel in open_channels:
    #     rmp_client.close_channel(channel, 0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    run()

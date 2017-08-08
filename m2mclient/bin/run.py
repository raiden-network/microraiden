#!/usr/bin/env python3

import click
import os

from m2mclient.m2mclient import M2MClient


@click.command()
@click.option('--api-endpoint', default='localhost', help='Address of the HTTP API server.')
@click.option('--api-port', default=5000)
@click.option('--datadir', default=os.path.join(os.path.expanduser('~'), '.raiden'), help='Raiden data directory.')
@click.option('--rpc-endpoint', default='localhost', help='Address of the Ethereum RPC server.')
@click.option('--rpc-port', default=8545, help='Ethereum RPC port.')
@click.option('--key-path', default='privkey.txt', help='Path to private key file.')
@click.option(
    '--channel-manager-address',
    default='0x1111111111111111111111111111111111111111',
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--channel-manager-abi-path',
    default='channel_manager_abi.json',
    help='Path to a file containing the channel manager ABI.'
)
@click.option(
    '--token-address',
    default='0x2608096b2aebd85bc3c61444ca43dc136cd5ced8',
    help='Ethereum address of the token contract.'
)
def run(
        api_endpoint,
        api_port,
        datadir,
        rpc_endpoint,
        rpc_port,
        key_path,
        channel_manager_address,
        channel_manager_abi_path,
        token_address
):
    client = M2MClient(
        api_endpoint,
        api_port,
        datadir,
        rpc_endpoint,
        rpc_port,
        key_path,
        channel_manager_address,
        channel_manager_abi_path,
        token_address
    )

    # client.request_resource('myresource')
    client.open_channel('0x1111111111111111111111111111111111111111', 200)


if __name__ == '__main__':
    run()

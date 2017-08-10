#!/usr/bin/env python3

import click
import os

from raiden_mps.client.m2mclient import M2MClient
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS, TOKEN_ADDRESS


@click.command()
@click.option('--api-endpoint', default='localhost', help='Address of the HTTP API server.')
@click.option('--api-port', default=5000)
@click.option('--datadir', default=os.path.join(os.path.expanduser('~'), '.raiden'), help='Raiden data directory.')
@click.option('--rpc-endpoint', default='localhost', help='Address of the Ethereum RPC server.')
@click.option('--rpc-port', default=8545, help='Ethereum RPC port.')
@click.option('--key-path', help='Path to private key file.')
@click.option('--dry-run', default=False, is_flag=True, help='Create and sign transactions without sending them.')
@click.option(
    '--channel-manager-address',
    default=CHANNEL_MANAGER_ADDRESS,
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--contract-abi-path',
    help='Path to a file containing the ABIs for the token and channel manager.'
)
@click.option(
    '--token-address',
    default=TOKEN_ADDRESS,
    help='Ethereum address of the token contract.'
)
def run(
        api_endpoint,
        api_port,
        datadir,
        rpc_endpoint,
        rpc_port,
        key_path,
        dry_run,
        channel_manager_address,
        contract_abi_path,
        token_address
):
    client = M2MClient(
        api_endpoint,
        api_port,
        datadir,
        rpc_endpoint,
        rpc_port,
        key_path,
        dry_run,
        channel_manager_address,
        contract_abi_path,
        token_address
    )

    client.request_resource('doggo.jpg')
    channel = client.channels[0]
    client.close_channel(channel)


if __name__ == '__main__':
    run()

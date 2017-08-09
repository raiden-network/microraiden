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
    default='0x94856f00a8097103c4b623ede4a240f934b1062f',
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--contract-abi-path',
    default='../../contracts/build/contracts.json',
    help='Path to a file containing the ABIs for the token and channel manager.'
)
@click.option(
    '--token-address',
    default='0x90b90fa4f747d93d11a1401569b73e96689e0ed2',
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
        channel_manager_address,
        contract_abi_path,
        token_address
    )

    # client.request_resource('myresource')
    client.open_channel('0xd1bf222ef7289ae043b723939d86c8a91f3aac3f', 10)


if __name__ == '__main__':
    run()

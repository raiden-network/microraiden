#!/usr/bin/env python3

import click
import os

from m2mclient import M2MClient


@click.command()
@click.option('--api-endpoint', default='localhost', help='Address of the HTTP API server.')
@click.option('--api-port', default=5000)
@click.option('--datadir', default=os.path.join(os.path.expanduser('~'), '.raiden'), help='Raiden data directory.')
@click.option('--rpc-endpoint', default='localhost', help='Address of the Ethereum RPC server.')
@click.option('--rpc-port', default=8545, help='Ethereum RPC port.')
@click.option('--key-path', default='m2mclient/privkey.txt', help='Path to private key file.')
@click.option(
    '--channel-manager-address',
    default='0x0d43084eef59dc59ba378129e918e2707c209bc5',
    help='Ethereum address of the channel manager contract.'
)
@click.option(
    '--contract-abi-path',
    default='contracts/build/contracts.json',
    help='Path to a file containing the ABIs for the token and channel manager.'
)
@click.option(
    '--token-address',
    default='0x4baf3ed928b01beb1b47818a39beebaef008fbdb',
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

    #client.request_resource('myresource')
    # client.open_channel('0xd1bf222ef7289ae043b723939d86c8a91f3aac3f', 10)


if __name__ == '__main__':
    run()

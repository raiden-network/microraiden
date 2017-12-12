import logging
from itertools import count
import os
import sys
import gevent
import traceback

import click
from eth_utils import (
    decode_hex,
    is_same_address,
)
from ethereum.tester import TransactionFailed
from web3 import Web3, HTTPProvider, RPCProvider
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput

from microraiden import (
    config,
    utils,
)
from microraiden.channel_manager import ChannelManagerState
from microraiden.utils import create_signed_contract_transaction, privkey_to_addr
from microraiden.exceptions import StateFileException
from microraiden.make_helpers import make_channel_manager_contract

log = logging.getLogger('close_all_channels')


@click.command()
@click.option(
    '--rpc-provider',
    default=config.WEB3_PROVIDER_DEFAULT,
    help='Address of the Ethereum RPC provider'
)
@click.option(
    '--private-key',
    required=True,
    help='Path to private key file of the proxy',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--private-key-password-file',
    default=None,
    help='Path to file containing password for the JSON-encoded private key',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--state-file',
    default=None,
    help='State file of the proxy'
)
@click.option(
    '--channel-manager-address',
    default=None,
    help='Ethereum address of the channel manager contract'
)
def main(
        rpc_provider: RPCProvider,
        private_key: str,
        private_key_password_file: str,
        state_file: str,
        channel_manager_address: str
):
    private_key = utils.get_private_key(private_key, private_key_password_file)
    if private_key is None:
        sys.exit(1)

    receiver_address = privkey_to_addr(private_key)
    channel_manager_address = channel_manager_address or config.CHANNEL_MANAGER_ADDRESS

    if not state_file:
        state_file_name = "%s_%s.json" % (channel_manager_address[:10], receiver_address[:10])
        app_dir = click.get_app_dir('microraiden')
        state_file = os.path.join(app_dir, state_file_name)

    web3 = Web3(HTTPProvider(rpc_provider, request_kwargs={'timeout': 60}))
    web3.eth.defaultAccount = receiver_address
    channel_manager_contract = make_channel_manager_contract(web3, config.CHANNEL_MANAGER_ADDRESS)

    try:
        click.echo('Loading state file from {}'.format(state_file))
        state = ChannelManagerState.load(state_file)
    except StateFileException:
        click.echo('Error reading state file')
        traceback.print_exc()
        sys.exit(1)
    if not is_same_address(state.receiver, receiver_address):
        click.echo('Private key does not match receiver address in state file')
        sys.exit(1)
    elif not is_same_address(state.contract_address, channel_manager_address):
        click.echo('Channel manager contract address mismatch')
        sys.exit(1)

    click.echo('Closing all open channels with valid balance proofs for '
               'receiver {}'.format(receiver_address))
    close_open_channels(private_key, state, channel_manager_contract)


def close_open_channels(
        private_key: str,
        state: ChannelManagerState,
        channel_manager_contract: Contract,
        repetitions=None,
        wait=lambda: gevent.sleep(1)
):
    web3 = channel_manager_contract.web3
    channels_with_balance_proof = [
        c for c in state.channels.values() if c.last_signature is not None
    ]
    n_channels = len(state.channels)
    n_no_balance_proof = len(state.channels) - len(channels_with_balance_proof)
    n_txs_sent = 0
    pending_txs = {}

    if repetitions:
        iterator = range(repetitions)
    else:
        iterator = count()
    for _ in iterator:
        n_non_existant = 0
        n_invalid_balance_proof = 0
        for channel in channels_with_balance_proof:
            # lookup channel on block chain
            channel_id = (channel.sender, channel.receiver, channel.open_block_number)
            try:
                channel_info = channel_manager_contract.call().getChannelInfo(*channel_id)
            except (BadFunctionCallOutput, TransactionFailed):
                n_non_existant += 1
                continue
            _, deposit, settle_block_number, closing_balance = channel_info

            is_valid = channel.balance <= deposit
            n_invalid_balance_proof += int(not is_valid)
            close_sent = (channel.sender, channel.open_block_number) in pending_txs

            # send close if open or settling with wrong balance, unless already done
            if not close_sent and is_valid:
                raw_tx = create_signed_contract_transaction(
                    private_key,
                    channel_manager_contract,
                    'uncooperativeClose',
                    [
                        channel.receiver,
                        channel.open_block_number,
                        channel.balance,
                        decode_hex(channel.last_signature)
                    ]
                )
                tx_hash = web3.eth.sendRawTransaction(raw_tx)
                log.info('sending close tx (hash: {})'.format(tx_hash))
                pending_txs[channel.sender, channel.open_block_number] = tx_hash
                n_txs_sent += 1

        # print status
        msg_status = 'block: {}, pending txs: {}, total txs sent: {}'
        msg_progress = (
            'initial channels: {}, settled: {}, pending txs: {}, no BP: {}, invalid BP: {}'
        )
        log.info(msg_status.format(web3.eth.blockNumber, len(pending_txs), n_txs_sent))
        log.info(msg_progress.format(
            n_channels,
            n_non_existant,
            len(pending_txs),
            n_no_balance_proof,
            n_invalid_balance_proof
        ))

        # wait for next block
        block_before = web3.eth.blockNumber
        while web3.eth.blockNumber == block_before:
            wait()

        # update pending txs
        confirmed = []
        for channel_id, tx_hash in pending_txs.items():
            receipt = web3.eth.getTransactionReceipt(tx_hash)
            if receipt is None:
                continue
            tx = web3.eth.getTransaction(tx_hash)
            if receipt.gasUsed == tx.gas:
                raise ValueError('Transaction failed, out of gas (hash: {})'.format(tx_hash))
            confirmed.append(channel_id)
        for channel_id in confirmed:
            pending_txs.pop(channel_id)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

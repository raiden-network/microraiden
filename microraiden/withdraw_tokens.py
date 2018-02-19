import logging
import os
import sys
import gevent
import traceback

if __package__ is None:
    # add /microraiden/ to path
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    sys.path.insert(0, path)
    # remove /microraiden/microraiden/ from path
    path = os.path.abspath(os.path.dirname(__file__))
    if path in sys.path:
        sys.path.remove(path)

import click
from eth_utils import (
    decode_hex,
    encode_hex,
    is_same_address,
    denoms,
)
from ethereum.tester import TransactionFailed
from web3 import Web3, HTTPProvider
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput

from microraiden import (
    config,
    utils,
    constants,
)
from microraiden.channel_manager import ChannelManagerState
from microraiden.exceptions import StateFileException
from microraiden.make_helpers import make_channel_manager_contract

log = logging.getLogger('withdraw')


@click.command()
@click.option(
    '--rpc-provider',
    default=constants.WEB3_PROVIDER_DEFAULT,
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
@click.option(
    '--minimum-amount',
    default=1,
    type=int,
    help='Minimum amount in available balance in channel to trigger withdraw'
)
@click.option(
    '--gas-price',
    default=None,
    type=int,
    help='Gas price, in Gwei'
)
def main(
        rpc_provider: HTTPProvider,
        private_key: str,
        private_key_password_file: str,
        state_file: str,
        channel_manager_address: str,
        minimum_amount: int,
        gas_price: int,
):
    if minimum_amount <= 0:
        click.echo('Minimum amount need to be at least 1')
        sys.exit(1)
    private_key = utils.get_private_key(private_key, private_key_password_file)
    if private_key is None:
        sys.exit(1)

    receiver_address = utils.privkey_to_addr(private_key)

    web3 = Web3(HTTPProvider(rpc_provider, request_kwargs={'timeout': 60}))
    config.NETWORK_CFG.set_defaults(int(web3.version.network))
    web3.eth.defaultAccount = receiver_address
    channel_manager_address = (
        channel_manager_address or config.NETWORK_CFG.channel_manager_address
    )
    channel_manager_contract = make_channel_manager_contract(web3, channel_manager_address)

    if not state_file:
        state_file_name = "%s_%s.db" % (
            channel_manager_address[:10],
            receiver_address[:10]
        )
        app_dir = click.get_app_dir('microraiden')
        if not os.path.exists(app_dir):
            click.echo('No state file or directory found!')
            sys.exit(1)
        state_file = os.path.join(app_dir, state_file_name)

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

    click.echo('Withdrawing all paid tokens with at least {} due from '
               'receiver {}'.format(minimum_amount, receiver_address))
    withdraw_from_channels(
        private_key,
        state,
        channel_manager_contract,
        minimum_amount,
        gas_price * denoms.gwei if gas_price else None,
    )


def withdraw_from_channels(
        private_key: str,
        state: ChannelManagerState,
        channel_manager_contract: Contract,
        minimum: int = 1,
        gas_price: int = None,
        wait=lambda: gevent.sleep(1)
):
    web3 = channel_manager_contract.web3
    pending_txs = {}

    for channel in state.channels.values():
        if not channel.last_signature:
            continue

        channel_id = (channel.sender, channel.receiver, channel.open_block_number)
        try:
            channel_info = channel_manager_contract.call().getChannelInfo(*channel_id)
        except (BadFunctionCallOutput, TransactionFailed):
            continue
        _, deposit, settle_block_number, closing_balance, transferred_tokens = channel_info
        available_tokens = channel.balance - transferred_tokens

        if not channel.balance <= deposit or available_tokens < minimum:
            log.info(
                'Not enough available balance: %d - %d = %d < %d',
                channel.balance,
                transferred_tokens,
                available_tokens,
                minimum
            )
            continue
        raw_tx = utils.create_signed_contract_transaction(
            private_key,
            channel_manager_contract,
            'withdraw',
            [
                channel.open_block_number,
                channel.balance,
                decode_hex(channel.last_signature)
            ],
            gas_price=gas_price,
        )
        tx_hash = web3.eth.sendRawTransaction(raw_tx)
        log.info(
            'Sending withdraw tx (hash: %s): %d from %r',
            encode_hex(tx_hash),
            available_tokens,
            channel_id
        )
        pending_txs[channel_id] = (tx_hash, available_tokens)

    success = 0
    total_tokens = 0
    total_gas = 0
    gas_price = 0
    for channel_id, withdraw_info in pending_txs.items():
        tx_hash, available_tokens = withdraw_info
        receipt = None
        # wait for tx to be mined
        while True:
            receipt = web3.eth.getTransactionReceipt(tx_hash)
            if not receipt or not receipt.blockNumber:
                wait()
            else:
                break
        tx = web3.eth.getTransaction(tx_hash)
        total_gas += receipt.gasUsed
        gas_price = tx.gasPrice
        if receipt.gasUsed == tx.gas or getattr(receipt, 'status', None) == 0:
            log.error(
                'Transaction failed (hash: %s, tokens: %d, channel: %r)',
                encode_hex(tx_hash),
                available_tokens,
                channel_id
            )
        else:
            log.info(
                'Transaction success (hash: %s, tokens: %d, channel: %r)',
                encode_hex(tx_hash),
                available_tokens,
                channel_id
            )
            success += 1
            total_tokens += available_tokens
    log.info(
        'FINISHED Withdraw: total tokens recovered: %d, '
        'transactions succeeded: %d, total gas cost: %s ETH',
        total_tokens,
        success,
        web3.fromWei(total_gas * gas_price, 'ether'),
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

'''
A simple Python script to deploy contracts and then do a smoke test for them.
'''
import click
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3

import math


def check_succesful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    '''See if transaction went through (Solidity code did not throw).
    :return: Transaction receipt
    '''
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo['gas'] != receipt['gasUsed']
    return receipt


@click.command()
@click.option(
    '--chain',
    default='kovan',
    help='Chain to deploy on: kovan | ropsten | testrpc'
)
@click.option(
    '--challenge-period',
    default=30,
    help='Challenge period in number of blocks.'
)
@click.option(
    '--supply',
    default=10000000,
    help='Token contract supply (number of total issued tokens).'
)
@click.option(
    '--token-name',
    default='RDNToken',
    help='Token contract name.'
)
@click.option(
    '--token-decimals',
    default=6,
    help='Token contract number of decimals.'
)
@click.option(
    '--token-symbol',
    default='RDN',
    help='Token contract symbol.'
)
@click.option(
    '--token-address',
    help='Already deployed token address.'
)
@click.option(
    '--senders',
    default='0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38,0xd1bf222ef7289ae043b723939d86c8a91f3aac3f,0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a,0x0052D7B657553E7f47239d8c4431Fef001A7f99c',
    help='Sender addresses for assigning tokens.'
)
def main(**kwargs):
    project = Project()

    # print(kwargs)
    chain_name = kwargs['chain']
    challenge_period = kwargs['challenge_period']
    supply = kwargs['supply']
    senders = kwargs['senders'].split(',')
    token_name = kwargs['token_name']
    token_decimals = kwargs['token_decimals']
    token_symbol = kwargs['token_symbol']
    token_address = kwargs['token_address']
    token_assign = math.floor(supply / len(senders))

    print("Make sure {} chain is running, you can connect to it, or you'll get timeout".format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        print('Web3 provider is', web3.currentProvider)

        if not token_address:
            token = chain.provider.get_contract_factory(token_name)
            txhash = token.deploy(args=[supply, token_name, token_decimals, token_symbol])
            receipt = check_succesful_tx(chain.web3, txhash, 250)
            token_address = receipt['contractAddress']
            print(token_name, ' address is', token_address)

        channel_factory = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
        txhash = channel_factory.deploy(args=[token_address, challenge_period])
        receipt = check_succesful_tx(chain.web3, txhash, 250)
        cf_address = receipt['contractAddress']
        print('RaidenMicroTransferChannels address is', cf_address)

        for sender in senders:
            token(token_address).transact({'from': web3.eth.accounts[0]}).transfer(sender, token_assign);

        print('Senders have each been issued', token_assign, ' tokens')


if __name__ == '__main__':
    main()

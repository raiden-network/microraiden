'''
A simple Python script to deploy contracts and then do a smoke test for them.
'''
import click
from populus import Project
import binascii
from ethereum.utils import encode_hex
from eth_utils import pad_left, remove_0x_prefix
from deploy.utils import createWallet
from utils import sign
from utils.utils import (
    check_succesful_tx,
    wait,
    pack
)


@click.command()
@click.option(
    '--chain',
    default='kovan',
    help='Chain to deploy on: kovan | ropsten | rinkeby | tester | privtest'
)
@click.option(
    '--owner',
    help='Contracts owner, default: web3.eth.accounts[0]'
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
    default='CustomToken',
    help='Token contract name.'
)
@click.option(
    '--token-decimals',
    default=18,
    help='Token contract number of decimals.'
)
@click.option(
    '--token-symbol',
    default='TKN',
    help='Token contract symbol.'
)
@click.option(
    '--token-address',
    help='Already deployed token address.'
)
@click.option(
    '--senders',
    default=0,
    help='Number of generated new address with assigned tokens.'
)
@click.option(
    '--sender-addresses',
    default=None,
    help='Sender addresses for assigning tokens, separated by a comma.'
)
def getTokens(**kwargs):
    project = Project()

    # print(kwargs)
    chain_name = kwargs['chain']
    owner = kwargs['owner']
    challenge_period = kwargs['challenge_period']
    supply = kwargs['supply']
    senders = kwargs['senders']
    sender_addresses = kwargs['sender_addresses']
    token_name = kwargs['token_name']
    token_decimals = kwargs['token_decimals']
    token_symbol = kwargs['token_symbol']
    token_address = kwargs['token_address']

    if sender_addresses:
        sender_addresses = sender_addresses.split(',')
    else:
        sender_addresses = []

    supply *= 10**(token_decimals)

    txn_wait = 250
    event_wait = 50
    if chain_name == 'rinkeby':
        txn_wait = 500
        event_wait = 500

    print('''Make sure {} chain is running, you can connect to it and it is synced,
          or you'll get timeout'''.format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        owner = owner or web3.eth.accounts[0]
        print('Web3 provider is', web3.currentProvider)

        token = chain.provider.get_contract_factory('CustomToken')

        if not token_address:
            txhash = token.deploy(args=[supply, token_name, token_symbol, token_decimals],
                                  transaction={'from': owner})
            receipt = check_succesful_tx(chain.web3, txhash, txn_wait)
            token_address = receipt['contractAddress']
            print(token_name, ' address is', token_address)

        channel_factory = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
        txhash = channel_factory.deploy(args=[token_address, challenge_period])

        print('RaidenMicroTransferChannels arguments', token_address, challenge_period)
        padded_token_address = pad_left(remove_0x_prefix(token_address), 64, '0')
        print('RaidenMicroTransferChannels abi encoded arguments:',
              encode_hex(pack(padded_token_address, challenge_period)))
        receipt = check_succesful_tx(chain.web3, txhash, txn_wait)
        cf_address = receipt['contractAddress']
        print('RaidenMicroTransferChannels address is', cf_address)

        if senders > 0 or len(sender_addresses) > 0:
            priv_keys = []
            addresses = []
            token_assign = int(supply / (len(sender_addresses) + senders))

            # we cannot retrieve private keys from configured chains
            # therefore: create 5 wallets (sample addresses with private keys)
            # store in separate arrays
            for i in range(senders - 1):
                priv_key, address = createWallet()
                priv_keys.append(priv_key)
                addresses.append('0x' + address)

            # send tokens to each new wallet
            for sender in addresses:
                token(token_address).transact({'from': owner}).transfer(sender, token_assign)
            # also send tokens to sender addresses
            for sender in sender_addresses:
                token(token_address).transact({'from': owner}).transfer(sender, token_assign)

                print('Senders have each been issued', token_assign, ' tokens')

            # check if it works:
            # 1. get message balance hash for address[0]
            balance_msg = "Receiver: " + addresses[0] + ", Balance: 10000, Channel ID: 100"
            # 2. sign the hash with private key corresponding to address[0]
            balance_msg_sig, addr = sign.check(balance_msg,
                                               binascii.unhexlify(remove_0x_prefix(priv_keys[0])))
            # 3. check if ECVerify and ec_recovered address are equal
            ec_recovered_addr = channel_factory(cf_address).call().verifyBalanceProof(addresses[0],
                                                                                      100, 10000,
                                                                                      balance_msg_sig)
            print('EC_RECOVERED_ADDR:', ec_recovered_addr)
            print('FIRST WALLET ADDR:', addresses[0])
            assert ec_recovered_addr == addresses[0]

            print('Wait for confirmation...')

            transfer_filter = token.on('Transfer')
            wait(transfer_filter, event_wait)

            print('BALANCE:', token(token_address).call().balanceOf(addresses[0]))
            assert token(token_address).call().balanceOf(addresses[0]) > 0

            # return arrays with generated wallets
            # (private keys first, then addresses, so that priv_key[0] <-> address[0]
            return (priv_keys, addresses, token(token_address))


if __name__ == '__main__':
    print(getTokens())

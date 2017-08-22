import os
import sys
import json

from raiden_mps.contract_proxy import ChannelContractProxy
from web3 import Web3
from web3.providers.rpc import RPCProvider

import logging

log = logging.getLogger(__name__)

from raiden_mps.channel_manager import (
    ChannelManager,
    StateReceiverAddrMismatch,
    StateContractAddrMismatch
)


def parse_balance_proof_msg(proxy, receiver, open_block_number, balance, signature):
    return proxy.verifyBalanceProof(receiver, open_block_number, balance, signature)


def make_contract_proxy(web3, private_key, contract_address):
    contracts_abi_path = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    return ChannelContractProxy(web3, private_key, contract_address, abi, int(20e9), 100000)


def make_channel_manager(private_key: str, state_filename: str, channel_contract_address: str):
    web3 = Web3(RPCProvider())
    try:
        return ChannelManager(
            web3,
            make_contract_proxy(web3, private_key, channel_contract_address),
            private_key,
            state_filename=state_filename,
            channel_contract_address=channel_contract_address
        )
    except StateReceiverAddrMismatch as e:
        log.error('Receiver address does not match address stored in a saved state. '
                  'Use a different file, or backup and remove %s. (%s)' %
                  (state_filename, e))
        sys.exit(1)

    except StateContractAddrMismatch as e:
        log.error('channel contract address mismatch. '
                  'Saved state file is %s. Backup it, remove, then'
                  'start proxy again (%s)' %
                  (state_filename, e))
        sys.exit(1)

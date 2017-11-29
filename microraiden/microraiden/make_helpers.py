import sys

from microraiden.contract_proxy import ChannelContractProxy
from web3 import Web3

import logging

log = logging.getLogger(__name__)

from microraiden.channel_manager import ChannelManager
from microraiden.exceptions import (
    StateReceiverAddrMismatch,
    StateContractAddrMismatch
)
from microraiden import config
from microraiden.proxy.paywalled_proxy import PaywalledProxy


def make_contract_proxy(web3, private_key, contract_address):
    metadata = config.CONTRACT_METADATA['RaidenMicroTransferChannels']
    return ChannelContractProxy(
        web3,
        private_key,
        contract_address,
        metadata['abi'],
        config.GAS_PRICE,
        config.GAS_LIMIT
    )


def make_channel_manager(private_key: str, contract_address: str, state_filename: str, web3):
    abi = config.CONTRACT_METADATA['RaidenMicroTransferChannels']['abi']
    channel_manager_proxy = make_contract_proxy(web3, private_key, contract_address)
    token_address = channel_manager_proxy.contract.call().token_address()
    token_contract = web3.eth.contract(abi=abi, address=token_address)
    try:
        return ChannelManager(
            web3,
            channel_manager_proxy,
            token_contract,
            private_key,
            state_filename=state_filename
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


def make_paywalled_proxy(private_key: str,
                         state_filename: str,
                         contract_address=config.CHANNEL_MANAGER_ADDRESS,
                         flask_app=None, web3=None):
    if web3 is None:
        web3 = Web3(config.WEB3_PROVIDER)
    channel_manager = make_channel_manager(private_key, contract_address, state_filename, web3)
    proxy = PaywalledProxy(channel_manager, flask_app, config.HTML_DIR, config.JSLIB_DIR)
    return proxy

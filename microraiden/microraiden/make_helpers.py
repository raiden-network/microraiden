import sys

from web3 import Web3, HTTPProvider

import logging

from web3.contract import Contract

log = logging.getLogger(__name__)

from microraiden.channel_manager import ChannelManager
from microraiden.exceptions import (
    StateReceiverAddrMismatch,
    StateContractAddrMismatch
)
from microraiden import config
from microraiden.proxy.paywalled_proxy import PaywalledProxy


def make_channel_manager_contract(web3: Web3, channel_manager_address: str) -> Contract:
    return web3.eth.contract(
        abi=config.CONTRACT_METADATA[config.CHANNEL_MANAGER_ABI_NAME]['abi'],
        address=channel_manager_address
    )


def make_channel_manager(
        private_key: str,
        channel_manager_address: str,
        state_filename: str,
        web3: Web3
) -> ChannelManager:
    channel_manager_contract = make_channel_manager_contract(web3, channel_manager_address)
    token_address = channel_manager_contract.call().token()
    token_abi = config.CONTRACT_METADATA[config.TOKEN_ABI_NAME]['abi']
    token_contract = web3.eth.contract(abi=token_abi, address=token_address)
    try:
        return ChannelManager(
            web3,
            channel_manager_contract,
            token_contract,
            private_key,
            state_filename=state_filename
        )
    except StateReceiverAddrMismatch as e:
        log.error(
            'Receiver address does not match address stored in a saved state. '
            'Use a different file, or backup and remove %s. (%s)' %
            (state_filename, e)
        )
        sys.exit(1)

    except StateContractAddrMismatch as e:
        log.error(
            'Channel contract address mismatch. '
            'Saved state file is %s. Backup it, remove, then start proxy again (%s)' %
            (state_filename, e)
        )
        sys.exit(1)


def make_paywalled_proxy(
        private_key: str,
        state_filename: str,
        contract_address=config.CHANNEL_MANAGER_ADDRESS,
        flask_app=None,
        web3=None
) -> PaywalledProxy:
    if web3 is None:
        web3 = Web3(HTTPProvider(config.WEB3_PROVIDER_DEFAULT, request_kwargs={'timeout': 60}))
    channel_manager = make_channel_manager(private_key, contract_address, state_filename, web3)
    proxy = PaywalledProxy(channel_manager, flask_app, config.HTML_DIR, config.JSLIB_DIR)
    return proxy

"""Helper functions to make initialization of the components simpler

Example::

    proxy = make_paywalled_proxy(receiver_privkey, '/tmp/proxy.db')
    """
import sys
import logging

from web3 import Web3, HTTPProvider
from web3.contract import Contract
from eth_utils import to_checksum_address

from microraiden.channel_manager import ChannelManager
from microraiden.exceptions import (
    StateReceiverAddrMismatch,
    StateContractAddrMismatch
)
from microraiden import constants
from microraiden.config import NETWORK_CFG
from microraiden.proxy.paywalled_proxy import PaywalledProxy

log = logging.getLogger(__name__)


def make_channel_manager_contract(web3: Web3, channel_manager_address: str) -> Contract:
    """
    Args:
        web3 (Web3): web3 provider
        channel_manager_address (str): channel manager contract to use
    Returns:
        Contract: contract wrapper class
    """
    channel_manager_address = to_checksum_address(channel_manager_address)
    return web3.eth.contract(
        abi=constants.CONTRACT_METADATA[constants.CHANNEL_MANAGER_ABI_NAME]['abi'],
        address=channel_manager_address
    )


def make_channel_manager(
        private_key: str,
        channel_manager_address: str,
        state_filename: str,
        web3: Web3
) -> ChannelManager:
    """
    Args:
        private_key (str): receiver's private key
        channel_manager_address (str): channel manager contract to use
        state_filename (str): path to the channel manager state database
        web3 (Web3): web3 provider
    Returns:
        ChannelManager: intialized and synced channel manager

    """
    channel_manager_address = to_checksum_address(channel_manager_address)
    channel_manager_contract = make_channel_manager_contract(web3, channel_manager_address)
    token_address = channel_manager_contract.call().token()
    token_abi = constants.CONTRACT_METADATA[constants.TOKEN_ABI_NAME]['abi']
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
        contract_address=None,
        flask_app=None,
        web3=None
) -> PaywalledProxy:
    """
    Args:
        private_key (str): receiver's private key
        state_filename (str): path to the state DB.
            If database doesn't exist, it'll be created and initialized.
        contract_address (str, optional): address of the channel manager contract.
        flask_app (optional): make proxy use this flask app
        web3 (Web3, optional): do not create a new web3 provider, but use this param instead
    Returns:
        PaywalledProxy: an initialized proxy.
        Do not forget to call `run()` to start serving requests.
    """
    if web3 is None:
        web3 = Web3(HTTPProvider(constants.WEB3_PROVIDER_DEFAULT, request_kwargs={'timeout': 60}))
        contract_address = contract_address or NETWORK_CFG.CHANNEL_MANAGER_ADDRESS
    channel_manager = make_channel_manager(private_key, contract_address, state_filename, web3)
    return PaywalledProxy(channel_manager, flask_app, constants.HTML_DIR, constants.JSLIB_DIR)

from web3 import Web3

from microraiden.constants import CONTRACT_METADATA, TOKEN_ABI_NAME, CHANNEL_MANAGER_ABI_NAME
from microraiden.utils import privkey_to_addr


class Context(object):
    def __init__(
            self,
            private_key: str,
            web3: Web3,
            channel_manager_address: str
    ):
        self.private_key = private_key
        self.address = privkey_to_addr(private_key)
        self.web3 = web3

        self.channel_manager = web3.eth.contract(
            address=channel_manager_address,
            abi=CONTRACT_METADATA[CHANNEL_MANAGER_ABI_NAME]['abi']
        )

        token_address = self.channel_manager.call().token()
        self.token = web3.eth.contract(
            address=token_address,
            abi=CONTRACT_METADATA[TOKEN_ABI_NAME]['abi']
        )

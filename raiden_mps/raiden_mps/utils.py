import os
import json
from raiden_mps.channel_manager import ChannelContractProxy
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS


def parse_balance_proof_msg(proxy, receiver, open_block_number, balance, signature):
    return proxy.verifyBalanceProof(receiver, open_block_number, balance, signature)


def get_contract_proxy(web3, private_key):
    contracts_abi_path = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    return ChannelContractProxy(web3, private_key, CHANNEL_MANAGER_ADDRESS, abi, int(20e9), 50000)

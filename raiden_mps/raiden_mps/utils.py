import os
import json

from raiden_mps.contract_proxy import ChannelContractProxy


def parse_balance_proof_msg(proxy, receiver, open_block_number, balance, signature):
    return proxy.verifyBalanceProof(receiver, open_block_number, balance, signature)


def get_contract_proxy(web3, private_key, contract_address):
    contracts_abi_path = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    return ChannelContractProxy(web3, private_key, contract_address, abi, int(20e9), 100000)

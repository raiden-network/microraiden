import rlp
from eth_utils import decode_hex
from ethereum.transactions import Transaction
from ethereum.utils import privtoaddr, encode_hex


class ContractProxy:
    def __init__(self, web3, privkey, contract_address, abi, gas_price, gas_limit):
        self.web3 = web3
        self.privkey = privkey
        self.address = contract_address
        self.abi = abi
        self.gas_price = gas_price
        self.gas_limit = gas_limit

    def create_contract_call(self, func_name, args, nonce_offset=0):
        caller_address = '0x' + encode_hex(privtoaddr(self.privkey))
        nonce = self.web3.eth.getTransactionCount(caller_address) + nonce_offset
        contract = self.web3.eth.contract(self.abi)
        data = contract._prepare_transaction(func_name, args)['data']
        data = decode_hex(data)
        tx = Transaction(nonce, self.gas_price, self.gas_limit, self.address, 0, data)
        return self.web3.toHex(rlp.encode(tx.sign(self.privkey)))

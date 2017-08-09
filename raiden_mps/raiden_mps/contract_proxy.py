from eth_utils import decode_hex
from ethereum.transactions import Transaction
from ethereum.utils import privtoaddr, encode_hex
import rlp
from web3.formatters import input_filter_params_formatter, log_array_formatter
from web3.utils.events import get_event_data
from web3.utils.filters import construct_event_filter_params
import time


class ContractProxy:
    def __init__(self, web3, privkey, contract_address, abi, gas_price, gas_limit):
        self.web3 = web3
        self.privkey = privkey
        self.caller_address = '0x' + encode_hex(privtoaddr(privkey))
        self.address = contract_address
        self.abi = abi
        self.contract = self.web3.eth.contract(self.abi)
        self.gas_price = gas_price
        self.gas_limit = gas_limit

    def create_transaction(self, func_name, args, nonce_offset=0):
        nonce = self.web3.eth.getTransactionCount(self.caller_address) + nonce_offset
        data = self.contract._prepare_transaction(func_name, args)['data']
        data = decode_hex(data)
        tx = Transaction(nonce, self.gas_price, self.gas_limit, self.address, 0, data)
        return self.web3.toHex(rlp.encode(tx.sign(self.privkey)))

    def get_logs(self, event_name, from_block=0, to_block='latest'):
        filter_kwargs = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': self.address
        }
        event_abi = [i for i in self.abi if i['type'] == 'event' and i['name'] == event_name][0]
        assert event_abi
        filter_ = construct_event_filter_params(event_abi, **filter_kwargs)[1]
        filter_params = [input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        logs = log_array_formatter(response)
        logs = [dict(log) for log in logs]
        for log in logs:
            log['args'] = get_event_data(event_abi, log)['args']
        return logs

    def get_event_blocking(self, event_name, condition=None, from_block=0, to_block='latest', wait=3, timeout=60):
        for i in range(0, timeout + wait, wait):
            logs = self.get_logs(event_name, from_block, to_block)
            matching_logs = [event for event in logs if not condition or condition(event)]
            if matching_logs:
                return matching_logs[0]
            elif i < timeout:
                time.sleep(wait)

        return None



class ChannelContractProxy(ContractProxy):
    def __init__(self, web3, privkey, contract_address, abi, gas_price, gas_limit):
        super().__init__(web3, privkey, contract_address, abi, gas_price, gas_limit)

    def get_channel_created_logs(self, from_block=0, to_block='latest'):
        return super().get_logs('ChannelCreated', from_block, to_block)

    def get_channel_close_requested_logs(self, from_block=0, to_block='latest'):
        return super().get_logs('ChannelCloseRequested', from_block, to_block)

    def get_channel_settled_logs(self, from_block=0, to_block='latest'):
        return super().get_logs('ChannelSettled', from_block, to_block)

    def get_channel_created_event_blocking(self, sender, receiver, from_block=0, to_block='latest', wait=3, timeout=60):
        def condition(event):
            return event['args']['_receiver'] == receiver and event['args']['_sender'] == sender

        return self.get_event_blocking('ChannelCreated', condition, from_block, to_block, wait, timeout)

    def get_channel_requested_close_event_blocking(self, sender, receiver, from_block=0, to_block='latest', wait=3, timeout=60):
        def condition(event):
            return event['args']['_receiver'] == receiver and event['args']['_sender'] == sender

        return self.get_event_blocking('ChannelCloseRequested', condition, from_block, to_block, wait, timeout)

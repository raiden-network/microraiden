import gevent
import rlp
from eth_utils import decode_hex, encode_hex
from ethereum.transactions import Transaction
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
from web3.formatters import input_filter_params_formatter, log_array_formatter
from web3.utils.empty import empty as web3_empty
from web3.utils.events import get_event_data
from web3.utils.filters import construct_event_filter_params

from microraiden.crypto import privkey_to_addr, sign_transaction

DEFAULT_TIMEOUT = 60
DEFAULT_RETRY_INTERVAL = 3


class ContractProxy:
    def __init__(self, web3: Web3, privkey, contract_address, abi, gas_price, gas_limit,
                 tester_mode=False) -> None:
        self.web3 = web3
        self.privkey = privkey
        self.caller_address = privkey_to_addr(privkey)
        if self.web3.eth.defaultAccount == web3_empty:
            self.web3.eth.defaultAccount = self.caller_address
        self.address = contract_address
        self.abi = abi
        self.contract = self.web3.eth.contract(abi=self.abi, address=contract_address)
        self.gas_price = gas_price
        self.gas_limit = gas_limit
        self.tester_mode = tester_mode

    def create_signed_transaction(self, func_name, args, nonce_offset=0, value=0):
        tx = self.create_transaction(func_name, args, nonce_offset, value)
        sign_transaction(tx, self.privkey, self.web3.version.network)
        return encode_hex(rlp.encode(tx))

    def create_transaction(self, func_name, args, nonce_offset=0, value=0):
        data = self.create_transaction_data(func_name, args)
        nonce = self.web3.eth.getTransactionCount(self.caller_address, 'pending') + nonce_offset
        tx = Transaction(nonce, self.gas_price, self.gas_limit, self.address, value, data)
        # v = CHAIN_ID according to EIP 155.
        tx.v = self.web3.version.network
        tx.sender = decode_hex(self.caller_address)
        return tx

    def create_transaction_data(self, func_name, args):
        data = self.contract._prepare_transaction(func_name, args)['data']
        return decode_hex(data)

    def get_logs(self, event_name, from_block=0, to_block='latest', filters=None):
        filter_kwargs = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': self.address
        }
        event_abi = [i for i in self.abi if i['type'] == 'event' and i['name'] == event_name][0]
        assert event_abi
        filters = filters if filters else {}
        filter_ = construct_event_filter_params(event_abi, argument_filters=filters,
                                                **filter_kwargs)[1]
        filter_params = input_filter_params_formatter(filter_)
        if not self.tester_mode:
            response = self.web3._requestManager.request_blocking('eth_getLogs', [filter_params])
        else:
            filter_ = self.web3.eth.filter(filter_params)
            response = self.web3.eth.getFilterLogs(filter_.filter_id)
            self.web3.eth.uninstallFilter(filter_.filter_id)

        logs = log_array_formatter(response)
        logs = [dict(log) for log in logs]
        for log in logs:
            log['args'] = get_event_data(event_abi, log)['args']
        return logs

    def get_event_blocking(
            self, event_name, from_block=0, to_block='pending', filters=None, condition=None,
            wait=DEFAULT_RETRY_INTERVAL, timeout=DEFAULT_TIMEOUT
    ):
        for i in range(0, timeout + wait, wait):
            logs = self.get_logs(event_name, from_block, to_block, filters)
            matching_logs = [event for event in logs if not condition or condition(event)]
            if matching_logs:
                return matching_logs[0]
            elif i < timeout:
                if not self.tester_mode:
                    gevent.sleep(wait)
                else:
                    self.web3.eth.mine(1)

        return None


class ChannelContractProxy(ContractProxy):
    def __init__(self, web3, privkey, contract_address, abi, gas_price, gas_limit,
                 tester_mode=False):
        super().__init__(web3, privkey, contract_address, abi, gas_price, gas_limit, tester_mode)

    def get_channel_created_logs(self, from_block=0, to_block='latest', filters=None):
        return self.get_logs('ChannelCreated', from_block, to_block, filters)

    def get_channel_topped_up_logs(self, from_block=0, to_block='latest', filters=None):
        return self.get_logs('ChannelToppedUp', from_block, to_block, filters)

    def get_channel_close_requested_logs(self, from_block=0, to_block='latest', filters=None):
        return self.get_logs('ChannelCloseRequested', from_block, to_block, filters)

    def get_channel_settled_logs(self, from_block=0, to_block='latest', filters=None):
        return self.get_logs('ChannelSettled', from_block, to_block, filters)

    def get_channel_topup_logs(self, from_block=0, to_block='latest', filters=None):
        return self.get_logs('ChannelToppedUp', from_block, to_block, filters)

    def get_channel_created_event_blocking(
            self, sender, receiver, from_block=0, to_block='latest',
            wait=DEFAULT_RETRY_INTERVAL, timeout=DEFAULT_TIMEOUT
    ):
        filters = {
            '_sender': sender,
            '_receiver': receiver
        }
        return self.get_event_blocking(
            'ChannelCreated', from_block, to_block, filters, None, wait, timeout
        )

    def get_channel_topped_up_event_blocking(
            self, sender, receiver, opening_block, deposit, topup,
            from_block=0, to_block='pending', wait=DEFAULT_RETRY_INTERVAL, timeout=DEFAULT_TIMEOUT
    ):
        filters = {
            '_sender': sender,
            '_receiver': receiver,
            '_open_block_number': opening_block
        }

        def condition(event):
            return (event['args']['_deposit'] == deposit and
                    event['args']['_added_deposit'] == topup)

        return self.get_event_blocking(
            'ChannelToppedUp', from_block, to_block, filters, condition, wait, timeout
        )

    def get_channel_close_requested_event_blocking(
            self, sender, receiver, opening_block,
            from_block=0, to_block='pending', wait=DEFAULT_RETRY_INTERVAL, timeout=DEFAULT_TIMEOUT
    ):
        filters = {
            '_sender': sender,
            '_receiver': receiver,
            '_open_block_number': opening_block
        }

        return self.get_event_blocking(
            'ChannelCloseRequested', from_block, to_block, filters, None, wait, timeout
        )

    def get_channel_settle_event_blocking(
            self, sender, receiver, opening_block,
            from_block=0, to_block='pending', wait=DEFAULT_RETRY_INTERVAL, timeout=DEFAULT_TIMEOUT
    ):
        filters = {
            '_sender': sender,
            '_receiver': receiver,
            '_open_block_number': opening_block
        }

        return self.get_event_blocking(
            'ChannelSettled', from_block, to_block, filters, None, wait, timeout
        )

    def get_settle_timeout(self, sender, receiver, open_block_number):
        try:
            channel_info = self.contract.call().getChannelInfo(sender, receiver, open_block_number)
        except BadFunctionCallOutput:
            # attempt to get info on a channel that doesn't exist
            return None
        return channel_info[2]

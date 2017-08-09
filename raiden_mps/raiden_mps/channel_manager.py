"""

"""
import json
import os
import pickle
import time
from ethereum.transactions import Transaction
from ethereum.utils import decode_hex
import gevent
import rlp
from web3 import Web3, formatters
from web3.providers.rpc import HTTPProvider, RPCProvider
from web3.utils.filters import construct_event_filter_params
from web3.utils.events import get_event_data
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS


def gen_balance_proof_msg(channel_id, amount):
    pass


def parse_balance_proof_msg(msg):
    """Returns tuple (sender, balance)"""
    return ("0x" + "5" * 40, 0)


def generate_signature(channel, private_key):
    assert False


class Blockchain(gevent.Greenlet):
    """
    Middleware which syncs the ChannelManager with the blockchain state
    """
    poll_freqency = 5

    def __init__(self, web3, contract):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract = contract
        self.cm = None

    def set_channel_manager(self, channel_manager):
        self.cm = channel_manager

    def _run(self):
        """
        coroutine
        which watches all events from contract_address, that involve self.address
        and updates ChannelManager
        """
        assert self.cm
        while True:
            self._update()
            gevent.sleep(self.poll_freqency)

    def _update(self):
        # check that history hasn't changed
        last_block = web3.eth.getBlock(self.cm.state.head_number)
        assert last_block.number == 0 or last_block.hash == self.cm.state.head_hash

        # filter for events after block_number
        block_range = {
            'from_block': self.cm.state.head_number + 1,
            'to_block': 'latest'
        }

        # channel created
        import ipdb; ipdb.set_trace()
        logs = contract_proxy.get_channel_created_logs(**block_range)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            sender = log['args']['_sender']
            deposit = log['args']['_deposit']
            open_block_number = log['blockNumber']
            self.cm.event_channel_opened(sender, open_block_number, deposit)

        # channel close requested
        logs = contract_proxy.get_channel_close_requested_logs(**block_range)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            balance = log['args']['_balance']
            self.cm.event_channel_opened(sender, open_block_number, balance, timeout)

        # channel closing requested event
        filter_ = construct_event_filter_params(channel_close_requested_event_abi,
                                                **filter_kwargs)[1]
        filter_params = [formatters.input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        for log in response:
            args = get_event_data(channel_created_event_abi, log)['args']
            if args['_receiver'] != self.cm.state.receiver:
                continue
            sender = args['_sender']
            open_block_number = args['open_block_number']
            balance = args['_balance']
            timeout = args['_timeout']
            self.cm.event_channel_close_requested(sender, open_block_number, balance, timeout)

        # channel settled event
        filter_ = construct_event_filter_params(channel_settled_event_abi, **filter_kwargs)[1]
        filter_params = [formatters.input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        for log in response:
            args = get_event_data(channel_created_event_abi, log)['args']
            if args['_receiver'] != self.cm.state.receiver:
                continue
            sender = args['_sender']
            open_block_number = args['_open_block_number']
            self.cm.event_channel_settled(sender, open_block_number)

        # update head hash and number
        block = web3.eth.getBlock('latest')
        self.cm.set_head(block.number, block.hash)


class ChannelManagerState(object):
    "Serializable Datastructure"

    def __init__(self, contract_address, receiver, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver.lower()
        self.head_hash = None
        self.head_number = 0
        self.channels = dict()
        self.filename = filename

    def store(self):
        if self.filename:
            pickle.dump(self, self.filename)

    @classmethod
    def load(cls, filename):
        return pickle.load(open(filename))


class ChannelManager(object):

    def __init__(self, blockchain, receiver, state_filename=None):
        self.blockchain = blockchain
        self.blockchain.set_channel_manager(self)
        # load state if file exists
        if state_filename is not None and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
            assert receiver == self.state.receiver
        else:
            self.state = ChannelManagerState(CHANNEL_MANAGER_ADDRESS, receiver, state_filename)

    def set_head(self, number, _hash):
        "should be called by blockchain after all events have been delivered, to trigger store"
        self.state.head_number = number
        self.state.head_hash = _hash
        self.state.store()

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender, open_block_number, deposit):
        assert sender not in self.state.channels  # shall we allow top-ups
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.state.channels[sender] = c
        self.state.store()

    def event_channel_close_requested(self, sender, open_block_number, balance, settle_timeout):
        "channel was closed by sender without consent"
        assert sender in self.state.channels
        c = self.state.channels[sender]
        assert c.open_block_number == open_block_number
        if c.balance > balance:
            self.close_channel(sender)  # dispute by closing the channel
        else:
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self.state.store()

    def event_channel_settled(self, sender, open_block_number):
        assert self.state.channels[sender].open_block_number == open_block_number
        del self.state.channels[sender]
        self.state.store()

    # end events ####

    def close_channel(self, sender):
        "receiver can always close the channel directly"
        c = self.state.channels[sender]
        # send closing tx
        signature = ''
        tx_params = [sender, c.open_block_number, c.balance, signature]
        self.web3.eth.sendRawTransaction(contract_proxy.create_contract_call('close', tx_params))
        # update local state
        c.is_closed = True
        self.state.store()

    def sign_close(self, sender):
        c = self.state.channels[sender]
        c.is_closed = True  # FIXME block number
        lm = c.last_message
        # return signed lm
        self.state.store()

    def get_token_balance(self):
        balance = 0
        for channel in self.state.channels.values():
            balance += channel.balance
        return balance

    def register_payment(self, msg):
        """
        registers a payment message
        returns its sender and value
        """
        sender, balance = parse_balance_proof_msg(msg)
        assert sender in self.state.channels
        c = self.state.channels[sender]
        assert c.balance < balance
        received = balance - c.balance
        c.balance = balance
        c.last_message = msg
        c.mtime = time.time()
        self.state.store()
        return (sender, received)


class Channel(object):

    def __init__(self, receiver, sender, deposit, open_block_number):
        self.receiver = receiver
        self.sender = sender  # sender address
        self.deposit = deposit
        self.open_block_number = open_block_number

        self.balance = 0
        self.is_closed = False
        self.last_message = None
        # if set, this is the absolut block_number where it can be settled
        self.settle_timeout = -1
        self.mtime = time.time()
        self.ctime = time.time()  # channel creation time


class PublicAPI(object):

    def __init__(self, channel_manager):
        assert isinstance(channel_manager, ChannelManager)
        self.cm = channel_manager

    def _channel(self, sender):
        return self.cm.state.channels[sender]

    def register_payment(self, msg):
        """
        registers a payment message
        returns its sender and value
        """
        return self.register_payment(msg)

    def get_balance(self, sender_address):
        "returns balance of address (i.e. total payed in current channel)"
        return self._channel(sender_address).balance

    def get_deposit(self, sender_address):
        "returns the deposit setup by address"
        return self._channel(sender_address).deposit

    def get_credit(self, sender_address):
        "returns the credit of address"
        return self.get_deposit(sender_address) - self.get_balance(sender_address)

    def settle(self, sender_address):
        "closes the channel, can directly be settled"
        self.cm.close_channel(sender_address)

    def sign_close(self, sender_address):
        "signs a cooperative close message (i.e. signs last message received by address)"
        return self.cm.sign_close(sender_address)

    def get_addresses(self):
        "returns the list of address that have an open channel"
        return self.cm.state.channels.keys()

    def outstanding_balance(self):
        "returns the not settled balance (i.e. the sum of balances of all open channels)"
        return sum(c.balance for c in self.cm.state.channels.values())

    def settled_balance(self):
        "returns the balance of server address at token"
        return self.cm.get_token_balance()

if __name__ == "__main__":
    # web3 = Web3(HTTPProvider('https://ropsten.infura.io/uKfMiq3I9Nk1ZkoRalwF'))
    web3 = Web3(RPCProvider())
    receiver = '0x004B52c58863C903Ab012537247b963C557929E8'
    contract_address = CHANNEL_MANAGER_ADDRESS
    contracts_abi_path = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    channel_created_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                    i['name'] == 'ChannelCreated')][0]
    channel_close_requested_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                            i['name'] == 'ChannelCloseRequested')][0]
    channel_settled_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                    i['name'] == 'ChannelSettled')][0]
    contract = web3.eth.contract(abi)(contract_address)
    private_key = 'secret'
    contract_proxy = ChannelContractProxy(web3, private_key, contract_address, abi, int(20e9), 50000)

    blockchain = Blockchain(web3, contract)
    channel_manager = ChannelManager(blockchain, receiver)
    blockchain.start()
    gevent.joinall([blockchain])

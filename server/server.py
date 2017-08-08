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


# web3 = Web3(HTTPProvider('https://ropsten.infura.io/uKfMiq3I9Nk1ZkoRalwF'))
web3 = Web3(RPCProvider())
receiver = ''
contract_address = '0xDFC2F3Adb77Be607C8C13e68fd0Cf9242b4925f7'.lower()
abi = json.loads("""[{"constant":true,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_token","type":"address"},{"name":"_value","type":"uint32"}],"name":"shaOfValue","outputs":[{"name":"data","type":"bytes32"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"_id","type":"bytes32"}],"name":"settle","outputs":[],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"_id","type":"bytes32"},{"name":"_balance","type":"uint32"},{"name":"_signature","type":"bytes"}],"name":"close","outputs":[],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"_receiver","type":"address"},{"name":"_token","type":"address"},{"name":"_deposit","type":"uint32"},{"name":"_challengePeriod","type":"uint8"}],"name":"init","outputs":[],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"_sender","type":"address"},{"name":"_receiver","type":"address"},{"name":"_token","type":"address"}],"name":"getChannel","outputs":[{"name":"","type":"bytes32"},{"name":"","type":"address"},{"name":"","type":"int256"},{"name":"","type":"int256"}],"payable":false,"type":"function"},{"inputs":[],"payable":false,"type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_sender","type":"address"},{"indexed":false,"name":"_receiver","type":"address"},{"indexed":false,"name":"_id","type":"bytes32"}],"name":"ChannelCreated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_sender","type":"address"},{"indexed":false,"name":"_receiver","type":"address"},{"indexed":false,"name":"_id","type":"bytes32"}],"name":"ChannelCloseRequested","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_sender","type":"address"},{"indexed":false,"name":"_receiver","type":"address"},{"indexed":false,"name":"_id","type":"bytes32"}],"name":"ChannelSettled","type":"event"}]""")
channel_created_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                i['name'] == 'ChannelCreated')][0]
channel_close_requested_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                        i['name'] == 'ChannelCloseRequested')][0]
channel_settled_event_abi = [i for i in abi if (i['type'] == 'event' and
                                                i['name'] == 'ChannelSettled')][0]
contract = web3.eth.contract(abi)
private_key = 'secret'


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
        # TODO: argument filters
        filter_kwargs = {
            'fromBlock': self.cm.state.head_number + 1,
            'toBlock': 'latest',
            'address': self.cm.state.contract_address
        }

        # channel opened event
        filter_ = construct_event_filter_params(channel_created_event_abi, **filter_kwargs)[1]
        filter_params = [formatters.input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        for log in response:
            assert not log.removed

        # channel closing requested event
        filter_ = construct_event_filter_params(channel_close_requested_event_abi,
                                                **filter_kwargs)[1]
        filter_params = [formatters.input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        for log in response:
            assert False

        # channel settled event
        filter_ = construct_event_filter_params(channel_settled_event_abi, **filter_kwargs)[1]
        filter_params = [formatters.input_filter_params_formatter(filter_)]
        response = self.web3._requestManager.request_blocking('eth_getLogs', filter_params)
        for log in response:
            assert False

        # update head hash and number
        block = web3.eth.getBlock('latest')
        self.cm.set_head(block.number, block.hash)


class ChannelManagerState(object):
    "Serializable Datastructure"

    def __init__(self, contract_address, receiver, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver
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
            self.state = ChannelManagerState(contract_address, receiver, state_filename)

    def set_head(self, number, _hash):
        "should be called by blockchain after all events have been delivered, to trigger store"
        self.state.head_number = number
        self.state.head_hash = _hash
        self.state.store()

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender, deposit):
        assert sender not in self.state.channels  # shall we allow top-ups
        c = Channel(self.state.receiver, sender, deposit)
        self.state.channels[sender] = c
        self.state.store()

    def event_channel_close_requested(self, sender, balance, settle_timeout):
        "channel was closed by sender without consent"
        assert sender in self.state.channels
        c = self.state.channels[sender]
        if c.balance > balance:
            self.close_channel(sender)  # dispute by closing the channel
        else:
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self.state.store()

    def event_channel_settled(self, sender):
        del self.state.channels[sender]
        self.state.store()

    # end events ####

    def close_channel(self, sender):
        "receiver can always close the channel directly"
        c = self.state.channels[sender]

        # prepare and send closing tx
        signature = generate_signature(c, private_key)
        tx_params = [sender, c.open_block_number, c.balance, signature]
        data = contract._encode_transaction_data('close', tx_params)['data']
        tx = Transaction(**{
            'nonce': self.web3.eth.getTransactionCount(self.state.receiver),
            'value': 0,
            'to': self.state.contract_address,
            'gasprice': 0,
            'startgas': 0,
            'data': decode_hex(data)
        })
        tx.sign(self.private_key)
        self.web3.eth.sendRawTransaction(web3.toHex(rlp.encode(tx)))

        # update local state
        c.is_closed = True
        self.state.store()

    def sign_close(self, sender):
        c = self.state.channels[sender]
        c.is_closed = True
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

    def __init__(self, receiver, sender, deposit):
        self.receiver = receiver
        self.sender = sender  # sender address
        self.deposit = deposit

        self.balance = 0
        self.is_closed = False
        self.last_message = None
        # if set, this is the absolut block_number where it can be settled
        self.settle_timeout = -1
        self.mtime = time.time()


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


blockchain = Blockchain(web3, contract)
channel_manager = ChannelManager(blockchain, receiver)
blockchain.start()
gevent.joinall([blockchain])

"""

"""
import time


def gen_balance_proof_msg(channel_id, amount):
    pass


def parse_balance_proof_msg(msg):
    pass


class Blockchain(object):
    """
    Middleware which syncs the ChannelManager with the blockchain state
    """
    cm = None
    poll_freqency = 5

    def __init__(self, web3_endpoint):
        self.web3_endpoint = web3_endpoint

    def set_channel_manager(self, channel_manager):
        self.cm = channel_manager

    def run(self, sync_from=0):
        """
        coroutine
        which watches all events from contract_address, that involve self.address
        and updates ChannelManager
        """
        assert self.cm
        while True:
            self._update()
            time.sleep(self.poll_freqency)

    def _update(self):
        contract_address = self.cm.contract_address
        address = self.cm.address
        head_number = self.cm.state.head_number
        head_hash = self.cm.state.head_hash
        # filter for events after block_number
        # which involve contract_address and address

        # update ChannelManager


class ChannelManagerState(object):
    "Serializable Datastructure"

    head_hash = ""
    head_number = 0

    def __init__(self, contract_address, address):
        self.contract_address = contract_address
        self.address = address
        self.channels = dict()


class ChannelManager(object):

    def __init__(self, address, blockchain, state_store_fn, init_contract_address=None):
        self.address = address
        self.blockchain = blockchain
        self.state_store_fn = state_store_fn
        if init_contract_address:
            self.state = ChannelManagerState(init_contract_address, address)
        else:
            self._load_state(state_store_fn)

    def _load_state(self):
        # init if not available
        assert self.state.address == self.address

    def _store_state(self):
        # should be called after every update
        pass

    def set_head(self, number, _hash):
        "should be called by blockchain after all events have been delivered, to trigger store"
        self.state.head_number = number
        self.state.head_hash = _hash
        self._store_state()

    def channel_opened(self, sender, deposit):
        assert sender not in self.state.channels  # shall we allow top-ups
        c = Channel(sender, deposit)
        self.state.channels[sender] = c

    def event_channel_close_requested(self, sender, balance, settle_timeout):
        "channel was closed by sender without consent"
        c = self.state.channels[sender]
        if c.balance > balance:
            self.close_channel(sender)  # dispute by closing the channel
        else:
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self._store_state()

    def event_channel_settled(self, sender):
        del self.state.channels[sender]
        self._store_state()

    def close_channel(self, sender):
        "receiver can always close the channel directly"
        c = self.state.channels[sender]
        c.is_closed = True
        self._store_state()
        # send tx with last balance

    def sign_close(self, sender):
        c = self.state.channels[sender]
        c.is_closed = True
        lm = c.last_message
        # return signed lm
        self._store_state()

    def get_token_balance(self):
        pass


class Channel(object):

    is_closed = False
    last_message = None
    balance = 0
    settle_timeout = -1  # if set, this is the absolut block_number where it can be settled

    def __init__(self, sender, deposit):
        self.sender = sender  # sender address
        self.deposit = deposit
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
        returns its value
        """
        sender, balance = parse_balance_proof_msg(msg)
        c = self._channel(sender)
        assert c.balance < balance
        received = balance - c.balance
        c.balance = balance
        c.last_message = msg
        return (received, sender)

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

"""

"""
import json
import os
import pickle
import time
from coincurve import PrivateKey
from ethereum.utils import privtoaddr, encode_hex
import gevent
from web3 import Web3
from web3.providers.rpc import HTTPProvider, RPCProvider
from raiden_mps.contract_proxy import ChannelContractProxy
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS


# TODO:
# - test
# - logging
# - distinguish channels between "opened n blocks ago", "opened, but not enough confirmations yet"
# - implement top ups
# - settle closed channels


class InvalidBalanceProof(Exception):
    pass


class NoOpenChannel(Exception):
    pass


class NoBalanceProofReceived(Exception):
    pass


class Blockchain(gevent.Greenlet):
    """
    Middleware which syncs the ChannelManager with the blockchain state
    """
    poll_freqency = 5

    def __init__(self, web3, contract_proxy, channel_manager):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract_proxy = contract_proxy
        self.cm = channel_manager

    def _run(self):
        """
        coroutine
        which watches all events from contract_address, that involve self.address
        and updates ChannelManager
        """
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
        logs = self.contract_proxy.get_channel_created_logs(**block_range)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            sender = log['args']['_sender']
            deposit = log['args']['_deposit']
            open_block_number = log['blockNumber']
            self.cm.event_channel_opened(sender, open_block_number, deposit)

        # channel close requested
        logs = self.contract_proxy.get_channel_close_requested_logs(**block_range)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            balance = log['args']['_balance']
            timeout = contract_proxy.get_settle_timeout(receiver, sender, open_block_number)
            self.cm.event_channel_opened(sender, open_block_number, balance, timeout)

        # channel settled event
        logs = self.contract_proxy.get_channel_settled_logs(**block_range)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            self.cm.event_channel_settled(sender, open_block_number)

        # update head hash and number
        block = self.web3.eth.getBlock('latest')
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


class ChannelManager(gevent.Greenlet):

    def __init__(self, web3, contract_proxy, receiver, private_key, state_filename=None):
        gevent.Greenlet.__init__(self)
        self.blockchain = Blockchain(web3, contract_proxy, self)
        self.receiver = receiver
        self.private_key = private_key
        self.contract_proxy = contract_proxy
        assert '0x' + encode_hex(privtoaddr(self.private_key)) == self.receiver.lower()

        if state_filename is not None and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
            assert receiver == self.state.receiver
        else:
            self.state = ChannelManagerState(CHANNEL_MANAGER_ADDRESS, receiver, state_filename)

    def _run(self):
        self.blockchain.start()
        gevent.joinall([self.blockchain])

    def set_head(self, number, _hash):
        "should be called by blockchain after all events have been delivered, to trigger store"
        self.state.head_number = number
        self.state.head_hash = _hash
        self.state.store()

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender, open_block_number, deposit):
        assert (sender, open_block_number) not in self.state.channels  # shall we allow top-ups
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.state.channels[(sender, open_block_number)] = c
        self.state.store()

    def event_channel_close_requested(self, sender, open_block_number, balance, settle_timeout):
        "channel was closed by sender without consent"
        assert (sender, open_block_number) in self.state.channels
        c = self.state.channels[(sender, open_block_number)]
        if c.balance > balance:
            self.close_channel(sender)  # dispute by closing the channel
        else:
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self.state.store()

    def event_channel_settled(self, sender, open_block_number):
        del self.state.channels[(sender, open_block_number)]
        self.state.store()

    # end events ####

    def close_channel(self, sender):
        "receiver can always close the channel directly"
        c = self.state.channels[sender]
        if c.last_signature is None:
            raise NoBalanceProofReceived('Cannot close a channel without a balance proof.')
        # send closing tx
        tx_params = [sender, c.open_block_number, c.balance, c.last_signature]
        raw_tx = self.contract_proxy.create_contract_call('close', tx_params)
        self.web3.eth.sendRawTransaction(raw_tx)
        # update local state
        c.is_closed = True
        self.state.store()

    def sign_close(self, sender, open_block_number, signature):
        if (sender, open_block_number) not in self.channels:
            raise NoOpenChannel('Channel does not exist or has been closed.')
        c = self.channels[(sender, open_block_number)]
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        if signature != c.last_signature:
            raise InvalidBalanceProof('Balance proof does not match latest one.')
        c.is_closed = True  # FIXME block number
        c.mtime = time.time()
        to_sign = self.contract_proxy.contract.call().closingAgreementMessageHash(signature)
        receiver_sig = PrivateKey.from_hex(self.private_key).sign(to_sign)
        recovered_receiver = self.contract_proxy.contract.call().verifyClosingSignature(
            signature, receiver_sig)
        assert recovered_receiver == self.receiver.lower()
        self.state.store()
        return receiver_sig

    def get_token_balance(self):
        balance = 0
        for channel in self.state.channels.values():
            balance += channel.balance
        return balance

    def verifyBalanceProof(self, receiver, open_block_number, balance, signature):
        """Verify that a balance proof is valid and return the sender.

        Does not check the balance itself.

        :returns: the channel
        """
        if receiver.lower() != self.receiver.lower():
            raise InvalidBalanceProof('Channel has wrong receiver.')
        signer = self.contract_proxy.contract.call().verifyBalanceProof(
            self.receiver, open_block_number, balance, signature)
        try:
            c = self.state.channels[(signer, open_block_number)]
        except KeyError:
            raise NoOpenChannel('Channel does not exist or has been closed.')
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        return c

    def register_payment(self, receiver, open_block_number, balance, signature):
        """
        registers a payment message
        returns its sender and value
        """
        c = self.verifyBalanceProof(receiver, open_block_number, balance, signature)
        if balance <= c.balance:
            raise InvalidBalanceProof('The balance must not increase.')
        received = balance - c.balance
        c.balance = balance
        c.last_signature = signature
        c.mtime = time.time()
        self.state.store()
        return (c.sender, received)


class Channel(object):

    def __init__(self, receiver, sender, deposit, open_block_number):
        self.receiver = receiver
        self.sender = sender  # sender address
        self.deposit = deposit
        self.open_block_number = open_block_number

        self.balance = 0
        self.is_closed = False
        self.last_signature = None
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
    sender = '0xd1Bf222EF7289ae043b723939d86c8A91f3AAC3F'
    contract_address = CHANNEL_MANAGER_ADDRESS
    contracts_abi_path = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
    abi = json.load(open(contracts_abi_path))['RaidenMicroTransferChannels']['abi']
    private_key = 'b6b2c38265a298a5dd24aced04a4879e36b5cc1a4000f61279e188712656e946'
    contract_proxy = ChannelContractProxy(web3, private_key, 2, abi, int(20e9),
                                          50000)
    channel_manager = ChannelManager(web3, contract_proxy, receiver, private_key)
    channel_manager.start()
    gevent.joinall([channel_manager])

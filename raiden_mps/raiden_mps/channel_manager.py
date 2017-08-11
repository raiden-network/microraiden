"""

"""
import os
import pickle
import time
from ethereum.utils import privtoaddr, encode_hex, decode_hex
import gevent
from raiden_mps.config import CHANNEL_MANAGER_ADDRESS
import logging


# TODO:
# - test
# - implement top ups
# - settle closed channels

logging.basicConfig(level=logging.DEBUG)


class InvalidBalanceProof(Exception):
    pass


class NoOpenChannel(Exception):
    pass


class NoBalanceProofReceived(Exception):
    pass


class Blockchain(gevent.Greenlet):
    """Class that watches the blockchain and relays events to the channel manager."""
    poll_freqency = 5

    def __init__(self, web3, contract_proxy, channel_manager, n_confirmations=5):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract_proxy = contract_proxy
        self.cm = channel_manager
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('blockchain')

    def _run(self):
        self.log.info('starting blockchain polling (frequency %ss)', self.poll_freqency)
        while True:
            self._update()
            gevent.sleep(self.poll_freqency)

    def _update(self):
        # check that history hasn't changed
        last_block = self.web3.eth.getBlock(self.cm.state.head_number)
        assert last_block.number == 0 or last_block.hash == self.cm.state.head_hash

        # filter for events after block_number
        filters_unconfirmed = {
            'from_block': self.cm.state.head_number + 1,
            'to_block': 'latest',
            'filters': {
                '_receiver': self.cm.state.receiver
            }
        }
        filters_confirmed = {
            'from_block': max(0, self.cm.state.head_number + 1 - self.n_confirmations),
            'to_block': max(self.web3.eth.blockNumber - self.n_confirmations, 0),
            'filters': {
                '_receiver': self.cm.state.receiver
            }
        }
#        self.log.debug('filtering for events u:%s-%s c:%s-%s',
#                       block_range_unconfirmed['from_block'], block_range_unconfirmed['to_block'],
#                       block_range_confirmed['from_block'], block_range_confirmed['to_block'])

        # unconfirmed channel created
        logs = self.contract_proxy.get_channel_created_logs(**filters_unconfirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            deposit = log['args']['_deposit']
            open_block_number = log['blockNumber']
            self.log.debug('received unconfirmed ChannelOpened event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.unconfirmed_event_channel_opened(sender, open_block_number, deposit)

        # channel created
        logs = self.contract_proxy.get_channel_created_logs(**filters_confirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            deposit = log['args']['_deposit']
            open_block_number = log['blockNumber']
            self.log.debug('received ChannelOpened event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.event_channel_opened(sender, open_block_number, deposit)

        # channel close requested
        logs = self.contract_proxy.get_channel_close_requested_logs(**filters_confirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            balance = log['args']['_balance']
            timeout = self.contract_proxy.get_settle_timeout(self.cm.state.receiver, sender,
                                                             open_block_number)
            self.log.debug('received ChannelCloseRequested event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.event_channel_close_requested(sender, open_block_number, balance, timeout)

        # channel settled event
        logs = self.contract_proxy.get_channel_settled_logs(**filters_confirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            self.log.debug('received ChannelSettled event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.event_channel_settled(sender, open_block_number)

        # update head hash and number
        block = self.web3.eth.getBlock('latest')
        self.cm.set_head(block.number, block.hash)


class ChannelManagerState(object):
    """The part of the channel manager state that needs to persist."""

    def __init__(self, contract_address, receiver, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver.lower()
        self.head_hash = None
        self.head_number = 0
        self.channels = dict()
        self.filename = filename
        self.log = logging.getLogger('channel_manager_state')
        self.unconfirmed_channels = dict()

    def store(self):
        """Store the state in a file."""
        if self.filename:
            self.log.debug('saving state in file')
            pickle.dump(self, self.filename)

    @classmethod
    def load(cls, filename):
        """Load a previously stored state."""
        return pickle.load(open(filename))


class ChannelManager(gevent.Greenlet):
    """Manages channels from the receiver's point of view."""

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

        self.log = logging.getLogger('channel_manager')
        self.log.info('setting up channel manager for %s', self.receiver)

    def _run(self):
        self.blockchain.start()
        gevent.joinall([self.blockchain])

    def set_head(self, number, _hash):
        """Set the block number up to which all events have been registered."""
        self.state.head_number = number
        self.state.head_hash = _hash
        self.state.store()

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender, open_block_number, deposit):
        """Notify the channel manager of a new confirmed channel opening."""
        assert (sender, open_block_number) not in self.state.channels
        self.state.unconfirmed_channels.pop((sender, open_block_number), None)
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.log.info('new channel opened (sender %s, block number %s)', sender, open_block_number)
        self.state.channels[(sender, open_block_number)] = c
        self.state.store()

    def unconfirmed_event_channel_opened(self, sender, open_block_number, deposit):
        """Notify the channel manager of a new channel opening that has not been confirmed yet."""
        assert (sender, open_block_number) not in self.state.channels
        assert (sender, open_block_number) not in self.state.unconfirmed_channels
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.state.unconfirmed_channels[(sender, open_block_number)] = c
        self.log.info('unconfirmed channel event received ')
        self.state.store()

    def event_channel_close_requested(self, sender, open_block_number, balance, settle_timeout):
        """Notify the channel manager that a the closing of a channel has been requested."""
        if not (sender, open_block_number) in self.state.channels:
            self.log.warn('attempt to close a non existing channel (sender %ss, block_number %ss)',
                          sender, open_block_number)
            return
        c = self.state.channels[(sender, open_block_number)]
        if c.balance > balance:
            self.log.info('sender tried to cheat, sending challenge (sender %s, block number %s)',
                          sender, open_block_number)
            self.close_channel(sender, open_block_number)  # dispute by closing the channel
        else:
            self.log.info('valid channel close request received (sender %s, block number %s)',
                          sender, open_block_number)
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self.state.store()

    def event_channel_settled(self, sender, open_block_number):
        """Notify the sender that a channel settlement."""
        self.log.info('Forgetting settled channel (sender %s, block number %s)',
                      sender, open_block_number)
        del self.state.channels[(sender, open_block_number)]
        self.state.store()

    # end events ####

    def close_channel(self, sender, open_block_number):
        """Close and settle a channel."""
        c = self.state.channels[(sender, open_block_number)]
        if c.last_signature is None:
            raise NoBalanceProofReceived('Cannot close a channel without a balance proof.')
        # send closing tx
        tx_params = [sender, open_block_number, c.balance, c.last_signature]
        raw_tx = self.contract_proxy.create_contract_call('close', tx_params)
        self.log.info('sending channel close transaction (sender %s, block number %s)',
                      sender, open_block_number)
        self.web3.eth.sendRawTransaction(raw_tx)
        # update local state
        c.is_closed = True
        self.state.store()

    def sign_close(self, sender, open_block_number, signature):
        """Sign an agreement for a channel closing."""
        if (sender, open_block_number) not in self.state.channels:
            raise NoOpenChannel('Channel does not exist or has been closed (sender=%s, open_block_number=%d)', sender, open_block_number)
        c = self.state.channels[(sender, open_block_number)]
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        assert signature is not None
        if c.last_signature is None:
            raise NoBalanceProofReceived('Payment has not been registered.')
        if signature != c.last_signature:
            raise InvalidBalanceProof('Balance proof does not match latest one.')
        c.is_closed = True  # FIXME block number
        c.mtime = time.time()
        receiver_sig = self.contract_proxy.sign_close(self.private_key, signature)
        recovered_receiver = self.contract_proxy.contract.call().verifyClosingSignature(
            signature, receiver_sig)
        assert recovered_receiver == self.receiver.lower()
        self.state.store()
        self.log.info('signed cooperative closing message (sender %s, block number %s)',
                      sender, open_block_number)
        return receiver_sig

    def get_token_balance(self):
        """Get the balance in all channels combined."""
        balance = 0
        for channel in self.state.channels.values():
            balance += channel.balance
        return balance

    def verify_balance_proof(self, receiver, open_block_number, balance, signature):
        """Verify that a balance proof is valid and return the sender.

        Does not check the balance itself.

        :returns: the channel
        """
        if receiver.lower() != self.receiver.lower():
            raise InvalidBalanceProof('Channel has wrong receiver.')
        signer = self.contract_proxy.contract.call().verifyBalanceProof(
            self.receiver, open_block_number, balance, decode_hex(signature))
        try:
            c = self.state.channels[(signer, open_block_number)]
        except KeyError:
            raise NoOpenChannel('Channel does not exist or has been closed (sender=%s, open_block_number=%d)', signer, open_block_number)
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        return c

    def register_payment(self, receiver, open_block_number, balance, signature):
        """Register a payment."""
        c = self.verify_balance_proof(receiver, open_block_number, balance, signature)
        if balance <= c.balance:
            raise InvalidBalanceProof('The balance must not increase.')
        received = balance - c.balance
        c.balance = balance
        c.last_signature = signature
        c.mtime = time.time()
        self.state.store()
        self.log.debug('registered payment (sender %s, block number %s, new balance %s)',
                       c.sender, open_block_number, balance)
        return (c.sender, received)

    def channels_to_dict(self):
        """Export all channels as a dictionary."""
        d = {}
        for sender, block_number in self.state.channels:
            channel = self.state.channels[(sender, block_number)]
            channel_dict = {
                'deposit': channel.deposit,
                'balance': channel.balance,
                'mtime': channel.mtime,
                'ctime': channel.ctime,
                'settle_timeout': channel.settle_timeout,
                'last_signature': channel.last_signature,
                'is_closed': channel.is_closed
            }
            if sender not in d:
                d[sender] = {}
            d[sender][block_number] = channel_dict
        return d

    def unconfirmed_channels_to_dict(self):
        """Export all unconfirmed channels as a dictionary."""
        d = {}
        for sender, block_number in self.state.unconfirmed_channels:
            channel = self.state.unconfirmed_channels[(sender, block_number)]
            channel_dict = {
                'deposit': channel.deposit,
                'ctime': channel.ctime
            }
            if sender not in d:
                d[sender] = {}
            d[sender][block_number] = channel_dict
        return d


class Channel(object):
    """A channel between two parties."""

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

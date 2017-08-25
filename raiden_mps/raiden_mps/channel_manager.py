"""

"""
import os
import pickle
import time
import tempfile
import shutil
import gevent
from eth_utils import decode_hex, is_same_address

import logging

from raiden_mps.crypto import sign_close, verify_closing_signature, verify_balance_proof, \
    privkey_to_addr

log = logging.getLogger(__name__)


class InvalidBalanceAmount(Exception):
    pass


class InvalidBalanceProof(Exception):
    pass


class NoOpenChannel(Exception):
    pass


class InsufficientConfirmations(Exception):
    pass


class NoBalanceProofReceived(Exception):
    pass


class StateContractAddrMismatch(Exception):
    pass


class StateReceiverAddrMismatch(Exception):
    pass


class Blockchain(gevent.Greenlet):
    """Class that watches the blockchain and relays events to the channel manager."""
    poll_frequency = 2

    def __init__(self, web3, contract_proxy, channel_manager, n_confirmations=5):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract_proxy = contract_proxy
        self.cm = channel_manager
        self.n_confirmations = n_confirmations
        self.log = log
        self.wait_sync_event = gevent.event.Event()

    def _run(self):
        self.log.info('starting blockchain polling (frequency %ss)', self.poll_frequency)
        while True:
            self._update()
            gevent.sleep(self.poll_frequency)

    def wait_sync(self):
        self.wait_sync_event.wait()

    def _update(self):
        # check that history hasn't changed
        last_block = self.web3.eth.getBlock(self.cm.state.head_number)
        assert last_block.number == 0 or last_block.hash == self.cm.state.head_hash
        current_block = self.web3.eth.blockNumber
        if current_block == self.cm.state.head_number:
            return

        # filter for events after block_number
        filters_confirmed = {
            'from_block': max(0, self.cm.state.head_number + 1 - self.n_confirmations),
            'to_block': max(current_block - self.n_confirmations, 0),
            'filters': {
                '_receiver': self.cm.state.receiver
            }
        }
        filters_unconfirmed = {
            'from_block': filters_confirmed['to_block'] + 1,
            'to_block': current_block,
            'filters': {
                '_receiver': self.cm.state.receiver
            }
        }
        self.log.debug('filtering for events u:%s-%s c:%s-%s @%d',
                       filters_unconfirmed['from_block'], filters_unconfirmed['to_block'],
                       filters_confirmed['from_block'], filters_confirmed['to_block'],
                       current_block)

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

        # unconfirmed channel top ups
        logs = self.contract_proxy.get_channel_topup_logs(**filters_unconfirmed)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            assert log['args']['_receiver'] == self.cm.state.receiver
            txhash = log['transactionHash']
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            deposit = log['args']['_deposit']
            added_deposit = log['args']['_added_deposit']
            self.log.debug('received top up event (sender %s, block number %s, deposit %s)',
                           sender, open_block_number, deposit)
            self.cm.unconfirmed_event_channel_topup(sender, open_block_number, txhash,
                                                    added_deposit, deposit)

        # confirmed channel top ups
        logs = self.contract_proxy.get_channel_topup_logs(**filters_confirmed)
        for log in logs:
            if log['args']['_receiver'] != self.cm.state.receiver:
                continue
            assert log['args']['_receiver'] == self.cm.state.receiver
            txhash = log['transactionHash']
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            deposit = log['args']['_deposit']
            added_deposit = log['args']['_added_deposit']
            self.log.debug('received top up event (sender %s, block number %s, deposit %s)',
                           sender, open_block_number, deposit)
            self.cm.event_channel_topup(sender, open_block_number, txhash, added_deposit, deposit)

        # channel settled event
        logs = self.contract_proxy.get_channel_settled_logs(**filters_confirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            self.log.debug('received ChannelSettled event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.event_channel_settled(sender, open_block_number)

        # channel close requested
        logs = self.contract_proxy.get_channel_close_requested_logs(**filters_confirmed)
        for log in logs:
            assert log['args']['_receiver'] == self.cm.state.receiver
            sender = log['args']['_sender']
            open_block_number = log['args']['_open_block_number']
            if (sender, open_block_number) not in self.cm.state.channels:
                continue
            balance = log['args']['_balance']
            timeout = self.contract_proxy.get_settle_timeout(
                sender, self.cm.state.receiver, open_block_number)
            if timeout is None:
                self.log.warn(
                    'received ChannelCloseRequested event for a channel that doesn\'t '
                    'exist or has been closed already (sender=%s open_block_number=%d)'
                    % (sender, open_block_number))
                self.cm.force_close_channel(sender, open_block_number)
                continue
            self.log.debug('received ChannelCloseRequested event (sender %s, block number %s)',
                           sender, open_block_number)
            self.cm.event_channel_close_requested(sender, open_block_number, balance, timeout)

        # update head hash and number
        block = self.web3.eth.getBlock(current_block)
        self.cm.set_head(block.number, block.hash)
        self.wait_sync_event.set()


class ChannelManagerState(object):
    """The part of the channel manager state that needs to persist."""

    def __init__(self, contract_address, receiver, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver.lower()
        self.head_hash = None
        self.head_number = 0
        self.channels = dict()
        self.filename = filename
        self.unconfirmed_channels = dict()

    def store(self):
        """Store the state in a file."""
        if self.filename:
            tmp = tempfile.NamedTemporaryFile()
            pickle.dump(self, tmp)
            tmp.flush()
            shutil.copyfile(tmp.name, self.filename)

    @classmethod
    def load(cls, filename):
        """Load a previously stored state."""
        assert filename is not None
        assert isinstance(filename, str)
        ret = pickle.load(open(filename, 'rb'))
        log.debug("loaded saved state. head_number=%d receiver=%s" %
                  (ret.head_number, ret.receiver))
        for sender, block in ret.channels.keys():
            log.debug("loaded channel info from the saved state sender=%s open_block=%s" %
                      (sender, block))
        return ret


class ChannelManager(gevent.Greenlet):
    """Manages channels from the receiver's point of view."""

    def __init__(self, web3, contract_proxy, token_contract, private_key: str,
                 state_filename=None):
        gevent.Greenlet.__init__(self)
        self.blockchain = Blockchain(web3, contract_proxy, self, n_confirmations=1)
        self.receiver = privkey_to_addr(private_key)
        self.private_key = private_key
        self.contract_proxy = contract_proxy
        self.token_contract = token_contract
        self.log = logging.getLogger('channel_manager')
        assert privkey_to_addr(self.private_key) == self.receiver.lower()

        channel_contract_address = contract_proxy.contract.address
        if state_filename is not None and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
        else:
            self.state = ChannelManagerState(channel_contract_address,
                                             self.receiver, state_filename)

        if not is_same_address(self.receiver, self.state.receiver):
            raise StateReceiverAddrMismatch('%s != %s' %
                                            (self.receiver.lower(), self.state.receiver))
        if not is_same_address(self.state.contract_address, channel_contract_address):
            raise StateContractAddrMismatch('%s != %s' % (
                channel_contract_address.lower(), self.state.contract_address.lower()))

        self.log.debug('setting up channel manager, receiver=%s channel_contract=%s' %
                       (self.receiver, channel_contract_address))

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
        self.state.channels[sender, open_block_number] = c
        self.state.store()

    def unconfirmed_event_channel_opened(self, sender, open_block_number, deposit):
        """Notify the channel manager of a new channel opening that has not been confirmed yet."""
        assert (sender, open_block_number) not in self.state.channels
        assert (sender, open_block_number) not in self.state.unconfirmed_channels
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.state.unconfirmed_channels[sender, open_block_number] = c
        self.log.info('unconfirmed channel event received (sender %s, block_number %s)',
                      sender, open_block_number)
        self.state.store()

    def event_channel_close_requested(self, sender, open_block_number, balance, settle_timeout):
        """Notify the channel manager that a the closing of a channel has been requested."""
        if (sender, open_block_number) not in self.state.channels:
            self.log.warn('attempt to close a non existing channel (sender %ss, block_number %ss)',
                          sender, open_block_number)
            return
        c = self.state.channels[sender, open_block_number]
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
        """Notify the channel manager that a channel has been settled."""
        self.log.info('Forgetting settled channel (sender %s, block number %s)',
                      sender, open_block_number)
        del self.state.channels[sender, open_block_number]
        self.state.store()

    def unconfirmed_event_channel_topup(self, sender, open_block_number, txhash, added_deposit,
                                        deposit):
        """Notify the channel manager of a topup with not enough confirmations yet."""
        if (sender, open_block_number) not in self.state.channels:
            assert (sender, open_block_number) in self.state.unconfirmed_channels
            self.log.info('Ignoring unconfirmed topup of unconfirmed channel '
                          '(sender %s, block number %s, aded %s)',
                          sender, open_block_number, added_deposit)
            return
        self.log.info('Registering unconfirmed deposit top up '
                      '(sender %s, block number %s, aded %s)',
                      sender, open_block_number, added_deposit)
        c = self.state.channels[sender, open_block_number]
        c.unconfirmed_event_channel_topups[txhash] = added_deposit
        self.state.store()

    def event_channel_topup(self, sender, open_block_number, txhash, added_deposit, deposit):
        """Notify the channel manager that the deposit of a channel has been topped up."""
        self.log.info('Registering deposit top up (sender %s, block number %s, new deposit %s)',
                      sender, open_block_number, deposit)
        assert (sender, open_block_number) in self.state.channels
        c = self.state.channels[sender, open_block_number]
        if c.is_closed is True:
            self.log.warn("Topup of an already closed channel (sender=%s open_block=%d)" %
                          (sender, open_block_number))
            return None
        assert c.deposit + added_deposit == deposit
        c.deposit = deposit
        c.unconfirmed_event_channel_topups.pop(txhash, None)
        self.state.store()

    # end events ####

    def close_channel(self, sender, open_block_number):
        """Close and settle a channel."""
        if not (sender, open_block_number) in self.state.channels:
            self.log.warn("attempt to close a non-registered channel (sender=%s open_block=%s" %
                          (sender, open_block_number))
            return
        c = self.state.channels[sender, open_block_number]
        if c.last_signature is None:
            raise NoBalanceProofReceived('Cannot close a channel without a balance proof.')
        # send closing tx
        tx_params = [self.state.receiver, open_block_number,
                     c.balance, decode_hex(c.last_signature)]
        raw_tx = self.contract_proxy.create_signed_transaction('close', tx_params)

        txid = self.blockchain.web3.eth.sendRawTransaction(raw_tx)
        self.log.info('sent channel close(sender %s, block number %s, tx %s)',
                      sender, open_block_number, txid)
        # update local state
        c.is_closed = True
        self.state.store()

    def force_close_channel(self, sender, open_block_number):
        """Forcibly remove a channel from our channel state"""
        try:
            self.close_channel(sender, open_block_number)
            return
        except NoBalanceProofReceived:
            c = self.state.channels[sender, open_block_number]
            c.is_closed = True
            self.state.store()

    def sign_close(self, sender, open_block_number, signature):
        """Sign an agreement for a channel closing."""
        if (sender, open_block_number) not in self.state.channels:
            raise NoOpenChannel('Channel does not exist or has been closed'
                                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        c = self.state.channels[sender, open_block_number]
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        assert signature is not None
        if c.last_signature is None:
            raise NoBalanceProofReceived('Payment has not been registered.')
        if signature != c.last_signature:
            raise InvalidBalanceProof('Balance proof does not match latest one.')
        c.is_closed = True  # FIXME block number
        c.mtime = time.time()
        receiver_sig = sign_close(self.private_key, decode_hex(signature.replace('0x', '')))
        recovered_receiver = verify_closing_signature(signature, receiver_sig)
        assert recovered_receiver == self.receiver.lower()
        self.state.store()
        self.log.info('signed cooperative closing message (sender %s, block number %s)',
                      sender, open_block_number)
        return receiver_sig

    def get_locked_balance(self):
        """Get the balance in all channels combined."""
        balance = 0
        for channel in self.state.channels.values():
            balance += channel.balance
        return balance

    def get_liquid_balance(self):
        """Get the balance of the receiver in the token contract (not locked in channels)."""
        balance = self.token_contract.call().balanceOf(self.receiver)
        return balance

    def verify_balance_proof(self, sender, open_block_number, balance, signature):
        """Verify that a balance proof is valid and return the sender.

        Does not check the balance itself.

        :returns: the channel
        """
        if (sender, open_block_number) in self.state.unconfirmed_channels:
            raise InsufficientConfirmations(
                'Insufficient confirmations for the channel '
                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        try:
            c = self.state.channels[sender, open_block_number]
        except KeyError:
            raise NoOpenChannel('Channel does not exist or has been closed'
                                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')

        signer = verify_balance_proof(
            self.receiver, open_block_number, balance,
            decode_hex(signature.replace('0x', '')),
            self.contract_proxy.address
        )
        if not is_same_address(signer, sender):
            raise InvalidBalanceProof('Recovered signer does not match the sender')
        return c

    def register_payment(self, sender, open_block_number, balance, signature):
        """Register a payment."""
        c = self.verify_balance_proof(sender, open_block_number, balance, signature)
        log.info(c.unconfirmed_event_channel_topups)
        if balance <= c.balance:
            raise InvalidBalanceAmount('The balance must not decrease.')
        if balance > c.deposit:
            raise InvalidBalanceProof('Balance must not be greater than deposit')
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
            channel = self.state.channels[sender, block_number]
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
            channel = self.state.unconfirmed_channels[sender, block_number]
            channel_dict = {
                'deposit': channel.deposit,
                'ctime': channel.ctime
            }
            if sender not in d:
                d[sender] = {}
            d[sender][block_number] = channel_dict
        return d

    def wait_sync(self):
        self.blockchain.wait_sync()


class Channel(object):
    """A channel between two parties."""

    def __init__(self, receiver, sender, deposit, open_block_number):
        self.receiver = receiver
        self.sender = sender  # sender address
        self.deposit = deposit  # deposit is maximum funds that can be used
        self.open_block_number = open_block_number

        self.balance = 0  # how much of the deposit has been spent
        self.is_closed = False
        self.last_signature = None
        # if set, this is the absolut block_number where it can be settled
        self.settle_timeout = -1
        self.mtime = time.time()
        self.ctime = time.time()  # channel creation time

        self.unconfirmed_event_channel_topups = {}  # txhash to added deposit

    def toJSON(self):
        return self.__dict__

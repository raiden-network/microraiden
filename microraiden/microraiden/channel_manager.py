"""

"""
import os
import pickle
import time
import tempfile
import shutil
import gevent
import gevent.event
import filelock
from eth_utils import decode_hex, is_same_address

import logging

from microraiden.crypto import sign_balance_proof, verify_balance_proof, privkey_to_addr
from microraiden.utils import is_secure_statefile

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


class StateFileLocked(Exception):
    pass


class InsecureStateFile(Exception):
    pass


class Blockchain(gevent.Greenlet):
    """Class that watches the blockchain and relays events to the channel manager."""
    poll_frequency = 2

    def __init__(self, web3, contract_proxy, channel_manager, n_confirmations):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract_proxy = contract_proxy
        self.cm = channel_manager
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('blockchain')
        self.wait_sync_event = gevent.event.Event()
        self.running = False

    def _run(self):
        self.running = True
        self.log.info('starting blockchain polling (frequency %ss)', self.poll_frequency)
        while self.running:
            self._update()
            gevent.sleep(self.poll_frequency)
        self.log.info('stopped blockchain polling')

    def stop(self):
        self.running = False

    def wait_sync(self):
        self.wait_sync_event.wait()

    def _update(self):
        # reset unconfirmed channels in case of reorg
        if self.wait_sync_event.is_set():  # but not on first sync
            if self.web3.eth.blockNumber < self.cm.state.unconfirmed_head_number:
                self.log.info('chain reorganization detected, resyncing unconfirmed events')
                self.cm.reset_unconfirmed()
            try:
                # raises if hash doesn't exist (i.e. block has been replaced)
                self.web3.eth.getBlock(self.cm.state.unconfirmed_head_hash)
            except ValueError:
                self.log.info('chain reorganization detected, resyncing unconfirmed events')
                self.cm.reset_unconfirmed()

            # in case of reorg longer than confirmation number fail
            try:
                self.web3.eth.getBlock(self.cm.state.confirmed_head_hash)
            except ValueError:
                self.log.critical('events considered confirmed have been reorganized')
                assert False
                # TODO: store balance proofs, resync, apply balance proofs

        if self.cm.state.confirmed_head_number is None:
            self.cm.state.confirmed_head_number = -1
        if self.cm.state.unconfirmed_head_number is None:
            self.cm.state.unconfirmed_head_number = -1
        current_block = self.web3.eth.blockNumber
        new_unconfirmed_head_number = current_block
        new_confirmed_head_number = max(current_block - self.n_confirmations, 0)

        # filter for events after block_number
        filters_confirmed = {
            'from_block': self.cm.state.confirmed_head_number + 1,
            'to_block': new_confirmed_head_number,
            'filters': {
                '_receiver': self.cm.state.receiver
            }
        }
        filters_unconfirmed = {
            'from_block': self.cm.state.unconfirmed_head_number + 1,
            'to_block': new_unconfirmed_head_number,
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
        new_unconfirmed_head_hash = self.web3.eth.getBlock(new_unconfirmed_head_number).hash
        new_confirmed_head_hash = self.web3.eth.getBlock(new_confirmed_head_number).hash
        self.cm.set_head(
            new_unconfirmed_head_number,
            new_unconfirmed_head_hash,
            new_confirmed_head_number,
            new_confirmed_head_hash
        )
        self.wait_sync_event.set()


class ChannelManagerState(object):
    """The part of the channel manager state that needs to persist."""

    def __init__(self, contract_address, receiver, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver.lower()
        self.confirmed_head_number = None
        self.confirmed_head_hash = None
        self.unconfirmed_head_number = None
        self.unconfirmed_head_hash = None
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
            shutil.copystat(tmp.name, self.filename)

    @classmethod
    def load(cls, filename):
        """Load a previously stored state."""
        assert filename is not None
        assert isinstance(filename, str)
        if not is_secure_statefile(filename):
            raise InsecureStateFile(filename)
        ret = pickle.load(open(filename, 'rb'))
        log.debug("loaded saved state. head_number=%d receiver=%s" %
                  (ret.confirmed_head_number, ret.receiver))
        for sender, block in ret.channels.keys():
            log.debug("loaded channel info from the saved state sender=%s open_block=%s" %
                      (sender, block))
        return ret


class ChannelManager(gevent.Greenlet):
    """Manages channels from the receiver's point of view."""

    def __init__(self, web3, contract_proxy, token_contract, private_key: str,
                 state_filename=None, n_confirmations=5) -> None:
        gevent.Greenlet.__init__(self)
        self.blockchain = Blockchain(web3, contract_proxy, self, n_confirmations=n_confirmations)
        self.receiver = privkey_to_addr(private_key)
        self.private_key = private_key
        self.contract_proxy = contract_proxy
        self.token_contract = token_contract
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('channel_manager')
        assert privkey_to_addr(self.private_key) == self.receiver.lower()

        channel_contract_address = contract_proxy.contract.address
        if state_filename is not None and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
        else:
            self.state = ChannelManagerState(channel_contract_address,
                                             self.receiver, state_filename)
        if state_filename is not None:
            self.lock_state = filelock.FileLock(state_filename)
            try:
                self.lock_state.acquire(timeout=0)
            except:
                raise StateFileLocked("state file %s is locked by another process" % state_filename)

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
        self.blockchain.get()  # re-raises exception

    def stop(self):
        if self.blockchain.running:
            self.blockchain.stop()
            self.blockchain.join()

    def set_head(self, unconfirmed_head_number, unconfirmed_head_hash,
                 confirmed_head_number, confirmed_head_hash):
        """Set the block number up to which all events have been registered."""
        self.state.unconfirmed_head_number = unconfirmed_head_number
        self.state.unconfirmed_head_hash = unconfirmed_head_hash
        self.state.confirmed_head_number = confirmed_head_number
        self.state.confirmed_head_hash = confirmed_head_hash
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

    def sign_close(self, sender, open_block_number, balance):
        """Sign an agreement for a channel closing."""
        if (sender, open_block_number) not in self.state.channels:
            raise NoOpenChannel('Channel does not exist or has been closed'
                                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        c = self.state.channels[sender, open_block_number]
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        assert balance is not None
        if c.last_signature is None:
            raise NoBalanceProofReceived('Payment has not been registered.')
        if balance != c.balance:
            raise InvalidBalanceProof('Requested closing balance does not match latest one.')
        c.is_closed = True  # FIXME block number
        c.mtime = time.time()
        receiver_sig = sign_balance_proof(
            self.private_key, self.receiver, open_block_number, balance
        )
        self.state.store()
        self.log.info('signed cooperative closing message (sender %s, block number %s)',
                      sender, open_block_number)
        return receiver_sig

    def get_locked_balance(self):
        """Get the balance in all channels combined."""
        return sum([c.balance for c in self.state.channels.values()])

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

        if not is_same_address(
                verify_balance_proof(
                    self.receiver, open_block_number, balance, decode_hex(signature)
                ),
                sender
        ):
            raise InvalidBalanceProof('Recovered signer does not match the sender')
        return c

    def register_payment(self, sender, open_block_number, balance, signature):
        """Register a payment."""
        c = self.verify_balance_proof(sender, open_block_number, balance, signature)
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

    def reset_unconfirmed(self):
        """Forget all unconfirmed channels and topups to allow for a clean resync."""
        self.state.unconfirmed_channels.clear()
        for channel in self.state.channels.values():
            channel.unconfirmed_event_channel_topups.clear()
        self.state.unconfirmed_head_number = self.state.confirmed_head_number
        self.state.unconfirmed_head_hash = self.state.confirmed_head_hash

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

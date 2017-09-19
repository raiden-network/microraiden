"""

"""
import os
import sys
import json
import time
import shutil
import gevent
import gevent.event
import filelock
import requests
import copy
from eth_utils import decode_hex, is_same_address

import logging

from microraiden.crypto import sign_balance_proof, verify_balance_proof, privkey_to_addr
from microraiden.utils import check_permission_safety
from microraiden.exceptions import (
    NetworkIdMismatch,
    StateReceiverAddrMismatch,
    StateContractAddrMismatch,
    StateFileLocked,
    NoOpenChannel,
    InsufficientConfirmations,
    InvalidBalanceProof,
    InvalidBalanceAmount,
    NoBalanceProofReceived,
    InsecureStateFile
)

log = logging.getLogger(__name__)


class Blockchain(gevent.Greenlet):
    """Class that watches the blockchain and relays events to the channel manager."""
    poll_interval = 2

    def __init__(self, web3, contract_proxy, channel_manager, n_confirmations,
                 sync_chunk_size=100 * 1000):
        gevent.Greenlet.__init__(self)
        self.web3 = web3
        self.contract_proxy = contract_proxy
        self.cm = channel_manager
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('blockchain')
        self.wait_sync_event = gevent.event.Event()
        self.is_connected = gevent.event.Event()
        self.sync_chunk_size = sync_chunk_size
        self.running = False

    def _run(self):
        self.running = True
        self.log.info('starting blockchain polling (interval %ss)', self.poll_interval)
        while self.running:
            try:
                self._update()
                self.is_connected.set()
                if self.wait_sync_event.is_set():
                    gevent.sleep(self.poll_interval)
            except requests.exceptions.ConnectionError as e:
                endpoint = self.web3.currentProvider.endpoint_uri
                self.log.warn("Ethereum node (%s) refused connection. Retrying in %d seconds." %
                              (endpoint, self.poll_interval))
                gevent.sleep(self.poll_interval)
                self.is_connected.clear()
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
                assert False  # unreachable as long as confirmation level is set high enough

        if self.cm.state.confirmed_head_number is None:
            self.cm.state.confirmed_head_number = -1
        if self.cm.state.unconfirmed_head_number is None:
            self.cm.state.unconfirmed_head_number = -1
        current_block = self.web3.eth.blockNumber
        new_unconfirmed_head_number = self.cm.state.unconfirmed_head_number + self.sync_chunk_size
        new_unconfirmed_head_number = min(new_unconfirmed_head_number, current_block)
        new_confirmed_head_number = max(new_unconfirmed_head_number - self.n_confirmations, 0)

        # return if blocks have already been processed
        if (self.cm.state.confirmed_head_number >= new_confirmed_head_number and
                self.cm.state.unconfirmed_head_number >= new_unconfirmed_head_number):
            return

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
            if (sender, open_block_number) not in self.cm.channels:
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
        try:
            new_unconfirmed_head_hash = self.web3.eth.getBlock(new_unconfirmed_head_number).hash
            new_confirmed_head_hash = self.web3.eth.getBlock(new_confirmed_head_number).hash
        except AttributeError:
            self.log.critical("RPC endpoint didn't return proper info for an existing block "
                              "(%d,%d)" % (new_unconfirmed_head_number, new_confirmed_head_number))
            self.log.critical("It is possible that the blockchain isn't fully synced. "
                              "This often happens when Parity is run with --fast or --warp sync.")
            self.log.critical("Can't continue - check status of the ethereum node.")
            sys.exit(1)
        self.cm.set_head(
            new_unconfirmed_head_number,
            new_unconfirmed_head_hash,
            new_confirmed_head_number,
            new_confirmed_head_hash
        )
        if not self.wait_sync_event.is_set() and new_unconfirmed_head_number == current_block:
            self.log.info('initial sync finished')
            self.wait_sync_event.set()


class ChannelManagerState(object):
    """The part of the channel manager state that needs to persist."""

    def __init__(self, contract_address, receiver, network_id, filename=None):
        self.contract_address = contract_address
        self.receiver = receiver.lower()
        self.confirmed_head_number = None
        self.confirmed_head_hash = None
        self.unconfirmed_head_number = None
        self.unconfirmed_head_hash = None
        self.channels = dict()
        self.filename = filename
        self.tmp_filename = None if self.filename is None else filename + '.tmp'
        self.unconfirmed_channels = dict()
        self.network_id = network_id

    def store(self):
        """Store the state in a file."""
        if self.filename:
            oldmask = os.umask(0o77)
            serialized_state = copy.deepcopy(self.__dict__)
            serialized_state['unconfirmed_channels'] = [
                v.__dict__ for v in serialized_state['unconfirmed_channels'].values()]
            serialized_state['channels'] = [
                v.__dict__ for v in serialized_state['channels'].values()]
            with open(self.tmp_filename, 'w') as f:
                json.dump(serialized_state, f)
                f.flush()
            shutil.copy2(self.tmp_filename, self.filename)
            os.umask(oldmask)

    @classmethod
    def load(cls, filename):
        """Load a previously stored state."""
        assert filename is not None
        assert isinstance(filename, str)
        if not check_permission_safety(filename):
            raise InsecureStateFile(filename)
        json_state = json.loads(open(filename, 'r').read())
        ret = cls.from_dict(json_state)
        log.debug("loaded saved state. head_number=%d receiver=%s" %
                  (ret.confirmed_head_number, ret.receiver))
        for sender, block in ret.channels.keys():
            log.debug("loaded channel info from the saved state sender=%s open_block=%s" %
                      (sender, block))
        return ret

    @classmethod
    def from_dict(cls, state: dict):
        ret = cls(state['contract_address'], state['receiver'], state['network_id'])
        ret.confirmed_head_number = state['confirmed_head_number']
        ret.confirmed_head_hash = state['confirmed_head_hash']
        ret.unconfirmed_head_number = state['unconfirmed_head_number']
        ret.unconfirmed_head_hash = state['unconfirmed_head_hash']
        ret.filename = state['filename']
        ret.tmp_filename = state['tmp_filename']
        for channel_dict in state['channels']:
            new_channel = Channel.from_dict(channel_dict)
            key = (new_channel.sender, new_channel.open_block_number)
            ret.channels[key] = new_channel
        return ret


class ChannelManager(gevent.Greenlet):
    """Manages channels from the receiver's point of view."""

    def __init__(self, web3, contract_proxy, token_contract, private_key: str,
                 state_filename=None, n_confirmations=1) -> None:
        gevent.Greenlet.__init__(self)
        self.blockchain = Blockchain(web3, contract_proxy, self, n_confirmations=n_confirmations)
        self.receiver = privkey_to_addr(private_key)
        self.private_key = private_key
        self.contract_proxy = contract_proxy
        self.token_contract = token_contract
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('channel_manager')
        network_id = web3.version.network
        assert privkey_to_addr(self.private_key) == self.receiver.lower()

        channel_contract_address = contract_proxy.contract.address
        if state_filename is not None and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
        else:
            self.state = ChannelManagerState(channel_contract_address,
                                             self.receiver, network_id,
                                             filename=state_filename)
        if state_filename is not None:
            self.lock_state = filelock.FileLock(state_filename)
            try:
                self.lock_state.acquire(timeout=0)
            except:
                raise StateFileLocked("state file %s is locked by another process" %
                                      state_filename)

        if network_id != self.state.network_id:
            raise NetworkIdMismatch("Network id mismatch: state=%d, backend=%d" % (
                                    self.state.network_id, network_id))

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
        if (sender, open_block_number) in self.channels:
            return  # ignore event if already provessed
        self.unconfirmed_channels.pop((sender, open_block_number), None)
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.log.info('new channel opened (sender %s, block number %s)', sender, open_block_number)
        self.channels[sender, open_block_number] = c
        self.state.store()

    def unconfirmed_event_channel_opened(self, sender, open_block_number, deposit):
        """Notify the channel manager of a new channel opening that has not been confirmed yet."""
        event_already_processed = (sender, open_block_number) in self.unconfirmed_channels
        channel_already_confirmed = (sender, open_block_number) in self.channels
        if event_already_processed or channel_already_confirmed:
            return
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        self.unconfirmed_channels[sender, open_block_number] = c
        self.log.info('unconfirmed channel event received (sender %s, block_number %s)',
                      sender, open_block_number)
        self.state.store()

    def event_channel_close_requested(self, sender, open_block_number, balance, settle_timeout):
        """Notify the channel manager that a the closing of a channel has been requested."""
        if (sender, open_block_number) not in self.channels:
            self.log.warn('attempt to close a non existing channel (sender %ss, block_number %ss)',
                          sender, open_block_number)
            return
        c = self.channels[sender, open_block_number]
        if c.balance > balance:
            self.log.info('sender tried to cheat, sending challenge (sender %s, block number %s)',
                          sender, open_block_number)
            self.close_channel(sender, open_block_number)  # dispute by closing the channel
        else:
            self.log.info('valid channel close request received (sender %s, block number %s)',
                          sender, open_block_number)
            c.settle_timeout = settle_timeout
            c.is_closed = True
            c.mtime = time.time()
        self.state.store()

    def event_channel_settled(self, sender, open_block_number):
        """Notify the channel manager that a channel has been settled."""
        self.log.info('Forgetting settled channel (sender %s, block number %s)',
                      sender, open_block_number)
        self.channels.pop((sender, open_block_number), None)
        self.state.store()

    def unconfirmed_event_channel_topup(self, sender, open_block_number, txhash, added_deposit,
                                        deposit):
        """Notify the channel manager of a topup with not enough confirmations yet."""
        if (sender, open_block_number) not in self.channels:
            assert (sender, open_block_number) in self.unconfirmed_channels
            self.log.info('Ignoring unconfirmed topup of unconfirmed channel '
                          '(sender %s, block number %s, aded %s)',
                          sender, open_block_number, added_deposit)
            return
        self.log.info('Registering unconfirmed deposit top up '
                      '(sender %s, block number %s, aded %s)',
                      sender, open_block_number, added_deposit)
        c = self.channels[sender, open_block_number]
        c.unconfirmed_topups[txhash] = added_deposit
        self.state.store()

    def event_channel_topup(self, sender, open_block_number, txhash, added_deposit, deposit):
        """Notify the channel manager that the deposit of a channel has been topped up."""
        self.log.info('Registering deposit top up (sender %s, block number %s, new deposit %s)',
                      sender, open_block_number, deposit)
        assert (sender, open_block_number) in self.channels
        c = self.channels[sender, open_block_number]
        if c.is_closed is True:
            self.log.warn("Topup of an already closed channel (sender=%s open_block=%d)" %
                          (sender, open_block_number))
            return None
        c.deposit = deposit
        c.unconfirmed_topups.pop(txhash, None)
        c.mtime = time.time()
        self.state.store()

    # end events ####

    def close_channel(self, sender, open_block_number):
        """Close and settle a channel."""
        if not (sender, open_block_number) in self.channels:
            self.log.warn("attempt to close a non-registered channel (sender=%s open_block=%s" %
                          (sender, open_block_number))
            return
        c = self.channels[sender, open_block_number]
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
        c.mtime = time.time()
        self.state.store()

    def force_close_channel(self, sender, open_block_number):
        """Forcibly remove a channel from our channel state"""
        try:
            self.close_channel(sender, open_block_number)
            return
        except NoBalanceProofReceived:
            c = self.channels[sender, open_block_number]
            c.is_closed = True
            self.state.store()

    def sign_close(self, sender, open_block_number, balance):
        """Sign an agreement for a channel closing."""
        if (sender, open_block_number) not in self.channels:
            raise NoOpenChannel('Channel does not exist or has been closed'
                                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        c = self.channels[sender, open_block_number]
        if c.is_closed:
            raise NoOpenChannel('Channel closing has been requested already.')
        assert balance is not None
        if c.last_signature is None:
            raise NoBalanceProofReceived('Payment has not been registered.')
        if balance != c.balance:
            raise InvalidBalanceProof('Requested closing balance does not match latest one.')
        c.is_closed = True
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
        return sum([c.balance for c in self.channels.values()])

    def get_liquid_balance(self):
        """Get the balance of the receiver in the token contract (not locked in channels)."""
        balance = self.token_contract.call().balanceOf(self.receiver)
        return balance

    def verify_balance_proof(self, sender, open_block_number, balance, signature):
        """Verify that a balance proof is valid and return the sender.

        Does not check the balance itself.

        :returns: the channel
        """
        if (sender, open_block_number) in self.unconfirmed_channels:
            raise InsufficientConfirmations(
                'Insufficient confirmations for the channel '
                '(sender=%s, open_block_number=%d)' % (sender, open_block_number))
        try:
            c = self.channels[sender, open_block_number]
        except KeyError:
            raise NoOpenChannel('Channel does not exist or has been closed'
                                '(sender=%s, open_block_number=%s)' % (sender, open_block_number))
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
        self.unconfirmed_channels.clear()
        for channel in self.channels.values():
            channel.unconfirmed_topups.clear()
        self.state.unconfirmed_head_number = self.state.confirmed_head_number
        self.state.unconfirmed_head_hash = self.state.confirmed_head_hash

    @property
    def channels(self):
        return self.state.channels

    @property
    def unconfirmed_channels(self):
        return self.state.unconfirmed_channels

    def channels_to_dict(self):
        """Export all channels as a dictionary."""
        d = {}
        for sender, block_number in self.channels:
            channel = self.channels[sender, block_number]
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
        for sender, block_number in self.unconfirmed_channels:
            channel = self.unconfirmed_channels[sender, block_number]
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

    def node_online(self):
        return self.blockchain.is_connected.is_set()


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

        self.unconfirmed_topups = {}  # txhash to added deposit

    @property
    def unconfirmed_deposit(self):
        return self.deposit + sum(self.unconfirmed_topups.values())

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, state: dict):
        ret = cls(None, None, None, None)
        assert (set(state) - set(ret.__dict__)) == set()
        for k, v in state.items():
            if k in ret.__dict__.keys():
                setattr(ret, k, v)
        return ret

"""Channel manager handles channel state changes on a low (blockchain) level."""
import time

import gevent
import gevent.event
import filelock
import logging
import os
from eth_utils import (
    decode_hex,
    is_same_address,
    is_checksum_address
)
from ethereum.exceptions import InsufficientBalance
from web3 import Web3
from web3.contract import Contract

from microraiden.utils import (
    verify_balance_proof,
    privkey_to_addr,
    sign_close,
    create_signed_contract_transaction
)
from microraiden.exceptions import (
    NetworkIdMismatch,
    StateReceiverAddrMismatch,
    StateContractAddrMismatch,
    StateFileLocked,
    NoOpenChannel,
    InsufficientConfirmations,
    InvalidBalanceProof,
    InvalidBalanceAmount,
    InvalidContractVersion,
    NoBalanceProofReceived,
)
from microraiden.constants import CHANNEL_MANAGER_CONTRACT_VERSION
from .state import ChannelManagerState
from .blockchain import Blockchain
from .channel import Channel, ChannelState

log = logging.getLogger(__name__)


class ChannelManager(gevent.Greenlet):
    """Manages channels from the receiver's point of view."""

    def __init__(
            self,
            web3: Web3,
            channel_manager_contract: Contract,
            token_contract: Contract,
            private_key: str,
            state_filename: str = None,
            n_confirmations=1
    ) -> None:
        gevent.Greenlet.__init__(self)
        self.blockchain = Blockchain(
            web3,
            channel_manager_contract,
            self,
            n_confirmations=n_confirmations
        )
        self.receiver = privkey_to_addr(private_key)
        self.private_key = private_key
        self.channel_manager_contract = channel_manager_contract
        self.token_contract = token_contract
        self.n_confirmations = n_confirmations
        self.log = logging.getLogger('channel_manager')
        network_id = int(web3.version.network)
        assert is_same_address(privkey_to_addr(self.private_key), self.receiver)

        # check contract version
        self.check_contract_version()

        if state_filename not in (None, ':memory:') and os.path.isfile(state_filename):
            self.state = ChannelManagerState.load(state_filename)
        else:
            self.state = ChannelManagerState(state_filename)
            self.state.setup_db(
                network_id,
                channel_manager_contract.address,
                self.receiver
            )

        assert self.state is not None
        if state_filename not in (None, ':memory:'):
            self.lock_state = filelock.FileLock(state_filename + '.lock')
            try:
                self.lock_state.acquire(timeout=0)
            except filelock.Timeout:
                raise StateFileLocked("state file %s is locked by another process" %
                                      state_filename)

        if network_id != self.state.network_id:
            raise NetworkIdMismatch("Network id mismatch: state=%d, backend=%d" % (
                                    self.state.network_id, network_id))

        if not is_same_address(self.receiver, self.state.receiver):
            raise StateReceiverAddrMismatch('%s != %s' %
                                            (self.receiver, self.state.receiver))
        if not is_same_address(self.state.contract_address, channel_manager_contract.address):
            raise StateContractAddrMismatch('%s != %s' % (
                channel_manager_contract.address, self.state.contract_address))

        self.log.debug('setting up channel manager, receiver=%s channel_contract=%s' %
                       (self.receiver, channel_manager_contract.address))

    def __del__(self):
        self.stop()

    def _run(self):
        self.blockchain.start()

    def stop(self):
        if self.blockchain.running:
            self.blockchain.stop()
            self.blockchain.join()

    def set_head(self,
                 unconfirmed_head_number: int,
                 unconfirmed_head_hash: int,
                 confirmed_head_number,
                 confirmed_head_hash):
        """Set the block number up to which all events have been registered."""
        assert unconfirmed_head_number > 0
        assert confirmed_head_number > 0
        assert confirmed_head_number < unconfirmed_head_number
        self.state.update_sync_state(unconfirmed_head_number=unconfirmed_head_number,
                                     unconfirmed_head_hash=unconfirmed_head_hash,
                                     confirmed_head_number=confirmed_head_number,
                                     confirmed_head_hash=confirmed_head_hash)

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender: str, open_block_number: int, deposit: int):
        """Notify the channel manager of a new confirmed channel opening."""
        assert is_checksum_address(sender)
        if (sender, open_block_number) in self.channels:
            return  # ignore event if already provessed
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        c.confirmed = True
        c.state = ChannelState.OPEN
        self.log.info('new channel opened (sender %s, block number %s)', sender, open_block_number)
        self.state.set_channel(c)

    def unconfirmed_event_channel_opened(self, sender: str, open_block_number: int, deposit: int):
        """Notify the channel manager of a new channel opening that has not been confirmed yet."""
        assert is_checksum_address(sender)
        assert deposit >= 0
        assert open_block_number > 0
        event_already_processed = (sender, open_block_number) in self.unconfirmed_channels
        channel_already_confirmed = (sender, open_block_number) in self.channels
        if event_already_processed or channel_already_confirmed:
            return
        c = Channel(self.state.receiver, sender, deposit, open_block_number)
        c.confirmed = False
        c.state = ChannelState.OPEN
        self.state.set_channel(c)
        self.log.info('unconfirmed channel event received (sender %s, block_number %s)',
                      sender, open_block_number)

    def event_channel_close_requested(
        self,
        sender: str,
        open_block_number: int,
        balance: int,
        settle_timeout: int
    ):
        """Notify the channel manager that a the closing of a channel has been requested.
        Params:
            settle_timeout (int):   settle timeout in blocks"""
        assert is_checksum_address(sender)
        assert settle_timeout >= 0
        if (sender, open_block_number) not in self.channels:
            self.log.warning(
                'attempt to close a non existing channel (sender %ss, block_number %ss)',
                sender,
                open_block_number
            )
            return
        c = self.channels[sender, open_block_number]
        if c.balance > balance:
            self.log.warning('sender tried to cheat, sending challenge '
                             '(sender %s, block number %s)',
                             sender, open_block_number)
            self.close_channel(sender, open_block_number)  # dispute by closing the channel
        else:
            self.log.info('valid channel close request received '
                          '(sender %s, block number %s, timeout %d)',
                          sender, open_block_number, settle_timeout)
            c.settle_timeout = settle_timeout
            c.is_closed = True
            c.confirmed = True
            c.mtime = time.time()
        self.state.set_channel(c)

    def event_channel_settled(self, sender, open_block_number):
        """Notify the channel manager that a channel has been settled."""
        assert is_checksum_address(sender)
        self.log.info('Forgetting settled channel (sender %s, block number %s)',
                      sender, open_block_number)
        self.state.del_channel(sender, open_block_number)

    def unconfirmed_event_channel_topup(
            self, sender, open_block_number, txhash, added_deposit
    ):
        """Notify the channel manager of a topup with not enough confirmations yet."""
        assert is_checksum_address(sender)
        if (sender, open_block_number) not in self.channels:
            assert (sender, open_block_number) in self.unconfirmed_channels
            self.log.info('Ignoring unconfirmed topup of unconfirmed channel '
                          '(sender %s, block number %s, added %s)',
                          sender, open_block_number, added_deposit)
            return
        self.log.info('Registering unconfirmed deposit top up '
                      '(sender %s, block number %s, added %s)',
                      sender, open_block_number, added_deposit)
        c = self.channels[sender, open_block_number]
        c.unconfirmed_topups[txhash] = added_deposit
        self.state.set_channel(c)

    def event_channel_topup(self, sender, open_block_number, txhash, added_deposit):
        """Notify the channel manager that the deposit of a channel has been topped up."""
        assert is_checksum_address(sender)
        self.log.info(
            'Registering deposit top up (sender %s, block number %s, added deposit %s)',
            sender, open_block_number, added_deposit
        )
        assert (sender, open_block_number) in self.channels
        c = self.channels[sender, open_block_number]
        if c.is_closed is True:
            self.log.warning(
                "Topup of an already closed channel (sender=%s open_block=%d)" %
                (sender, open_block_number)
            )
            return None
        c.deposit += added_deposit
        c.unconfirmed_topups.pop(txhash, None)
        c.mtime = time.time()
        self.state.set_channel(c)

    # end events ####

    def close_channel(self, sender: str, open_block_number: int):
        """Close and settle a channel.
        Params:
            sender (str):               sender address
            open_block_number (int):    block the channel was open in
        """
        assert is_checksum_address(sender)
        if not (sender, open_block_number) in self.channels:
            self.log.warning(
                "attempt to close a non-registered channel (sender=%s open_block=%s" %
                (sender, open_block_number)
            )
            return
        c = self.channels[sender, open_block_number]
        if c.last_signature is None:
            raise NoBalanceProofReceived('Cannot close a channel without a balance proof.')
        # send closing tx
        closing_sig = sign_close(
            self.private_key,
            sender,
            open_block_number,
            c.balance,
            self.channel_manager_contract.address
        )

        raw_tx = create_signed_contract_transaction(
            self.private_key,
            self.channel_manager_contract,
            'cooperativeClose',
            [
                self.state.receiver,
                open_block_number,
                c.balance,
                decode_hex(c.last_signature),
                closing_sig
            ]
        )

        # update local state
        c.is_closed = True
        c.mtime = time.time()
        self.state.set_channel(c)

        try:
            txid = self.blockchain.web3.eth.sendRawTransaction(raw_tx)
            self.log.info('sent channel close(sender %s, block number %s, tx %s)',
                          sender, open_block_number, txid)
        except InsufficientBalance:
            c.state = ChannelState.CLOSE_PENDING
            self.state.set_channel(c)
            raise

    def force_close_channel(self, sender: str, open_block_number: int):
        """Forcibly remove a channel from our channel state"""
        assert is_checksum_address(sender)
        try:
            self.close_channel(sender, open_block_number)
            return
        except NoBalanceProofReceived:
            c = self.channels[sender, open_block_number]
            c.is_closed = True
            self.state.set_channel(c)

    def sign_close(self, sender: str, open_block_number: int, balance: int):
        """Sign an agreement for a channel closing.
        Returns:
            channel close signature (str): a signature that can be used client-side to close
            the channel by directly calling contract's close method on-chain.
        """
        assert is_checksum_address(sender)
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
        receiver_sig = sign_close(
            self.private_key,
            sender,
            open_block_number,
            c.balance,
            self.channel_manager_contract.address
        )
        self.state.set_channel(c)
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

    def get_eth_balance(self):
        """Get eth balance of the receiver"""
        return self.channel_manager_contract.web3.eth.getBalance(self.receiver)

    def verify_balance_proof(self, sender, open_block_number, balance, signature):
        """Verify that a balance proof is valid and return the sender.

        This method just verifies if the balance proof is valid - no state update is performed.

        :returns: Channel, if it exists
        """
        assert is_checksum_address(sender)
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
                    self.receiver,
                    open_block_number,
                    balance,
                    decode_hex(signature),
                    self.channel_manager_contract.address
                ),
                sender
        ):
            raise InvalidBalanceProof('Recovered signer does not match the sender')
        return c

    def register_payment(self, sender: str, open_block_number: int, balance: int, signature: str):
        """Register a payment.
        Method will try to reconstruct (verify) balance update data
        with a signature sent by the client.
        If verification is succesfull, an internal payment state is updated.
        Parameters:
            sender (str):               sender of the balance proof
            open_block_number (int):    block the channel was opened in
            balance (int):              updated balance
            signature(str):             balance proof to verify
        """
        assert is_checksum_address(sender)
        c = self.verify_balance_proof(sender, open_block_number, balance, signature)
        if balance <= c.balance:
            raise InvalidBalanceAmount('The balance must not decrease.')
        if balance > c.deposit:
            raise InvalidBalanceProof('Balance must not be greater than deposit')
        received = balance - c.balance
        c.balance = balance
        c.last_signature = signature
        c.mtime = time.time()
        self.state.set_channel(c)
        self.log.debug('registered payment (sender %s, block number %s, new balance %s)',
                       c.sender, open_block_number, balance)
        return c.sender, received

    def reset_unconfirmed(self):
        """Forget all unconfirmed channels and topups to allow for a clean resync."""
        self.state.del_unconfirmed_channels()
        for channel in self.channels.values():
            channel.unconfirmed_topups.clear()
            self.state.set_channel(channel)
        self.state.unconfirmed_head_number = self.state.confirmed_head_number
        self.state.unconfirmed_head_hash = self.state.confirmed_head_hash

    @property
    def channels(self):
        return self.state.channels

    @property
    def unconfirmed_channels(self):
        return self.state.unconfirmed_channels

    @property
    def pending_channels(self):
        return self.state.pending_channels

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

    def get_token_address(self):
        return self.token_contract.address

    def check_contract_version(self):
        """Compare version of the contract to the version of the library.
        Only major and minor version is used in the comparison.
        """
        deployed_contract_version = self.channel_manager_contract.call().version()
        deployed_contract_version = deployed_contract_version.rsplit('.', 1)[0]
        library_version = CHANNEL_MANAGER_CONTRACT_VERSION.rsplit('.', 1)[0]
        if deployed_contract_version != library_version:
            raise InvalidContractVersion("Incompatible contract version: expected=%s deployed=%s" %
                                         (CHANNEL_MANAGER_CONTRACT_VERSION,
                                          deployed_contract_version))

    def close_pending_channels(self):
        """Close all channels that are in CLOSE_PENDING state.
        This state happens if the receiver's eth balance is not enough to
            close channel on-chain."""
        for sender, open_block_number in self.pending_channels.keys():
            self.close_channel(sender, open_block_number)  # dispute by closing the channel

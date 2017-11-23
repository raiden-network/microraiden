import requests
import sys
import gevent
import logging


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
                self.log.info('chain reorganization detected. '
                              'Resyncing unconfirmed events (%d < %d)' %
                              (self.web3.eth.blockNumber, self.cm.state.unconfirmed_head_number))
                self.cm.reset_unconfirmed()
            try:
                # raises if hash doesn't exist (i.e. block has been replaced)
                self.web3.eth.getBlock(self.cm.state.unconfirmed_head_hash)
            except ValueError:
                self.log.info('chain reorganization detected. '
                              'resyncing unconfirmed events (%d < %d). '
                              '(getBlock() raised ValueError)' %
                              (self.web3.eth.blockNumber, self.cm.state.unconfirmed_head_number))
                self.cm.reset_unconfirmed()

            # in case of reorg longer than confirmation number fail
            try:
                self.web3.eth.getBlock(self.cm.state.confirmed_head_hash)
            except ValueError:
                self.log.critical('events considered confirmed have been reorganized')
                assert False  # unreachable as long as confirmation level is set high enough

        if self.cm.state.confirmed_head_number is None:
            self.cm.state.update_sync_state(confirmed_head_number=-1)
        if self.cm.state.unconfirmed_head_number is None:
            self.cm.state.update_sync_state(unconfirmed_head_number=-1)
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
            self.wait_sync_event.set()

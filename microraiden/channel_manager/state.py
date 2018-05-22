"""Off-chain state is saved in a sqlite database."""
# import json
# import shutil
import sqlite3
import os
import logging
from eth_utils import is_address

from microraiden.utils import check_permission_safety

from microraiden.exceptions import (
    InsecureStateFile
)
from .channel import Channel, ChannelState

log = logging.getLogger(__name__)


def dict_factory(cursor, row):
    """make sqlite result a dict with keys being column names"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


DB_CREATION_SQL = """
CREATE TABLE `metadata` (
    `network_id`       INTEGER,
    `contract_address` CHAR(42),
    `receiver`         CHAR(42)
);
CREATE TABLE `syncstate` (
    `confirmed_head_number`   INTEGER,
    `confirmed_head_hash`     CHAR(66),
    `unconfirmed_head_number` INTEGER,
    `unconfirmed_head_hash`   CHAR(66)
);
-- deposit and balance have length of 78 to fit uint256
CREATE TABLE `channels` (
    `sender`            CHAR(42)        NOT NULL,
    `open_block_number` INTEGER         NOT NULL,
    `deposit`           DECIMAL(78,0)   NOT NULL,
    `balance`           DECIMAL(78,0)   NOT NULL,
    `last_signature`    CHAR(132),
    `settle_timeout`    INTEGER         NOT NULL,
    `mtime`             INTEGER         NOT NULL,
    `ctime`             INTEGER         NOT NULL,
    `state`             INTEGER         NOT NULL,
    `confirmed`         BOOL            NOT NULL,
    PRIMARY KEY (`sender`, `open_block_number`)
);
CREATE TABLE `topups` (
    `channel_rowid`     INTEGER,
    `txhash`            CHAR(66)        NOT NULL,
    `deposit`           DECIMAL(78,0)   NOT NULL,
    PRIMARY KEY (`channel_rowid`, `txhash`),
    FOREIGN KEY (`channel_rowid`) REFERENCES channels (rowid)
        ON DELETE CASCADE
);
INSERT INTO `metadata` VALUES (
    NULL,
    NULL,
    NULL
);
INSERT INTO `syncstate` VALUES (
    NULL,
    NULL,
    NULL,
    NULL
);
"""

UPDATE_METADATA_SQL = """
UPDATE `metadata` SET
    `network_id` = ?,
    `contract_address` = ?,
    `receiver` = ?;
"""

UPDATE_SYNCSTATE_SQL = {
    'confirmed_head_number': 'UPDATE `syncstate` SET `confirmed_head_number` = ?;',
    'confirmed_head_hash': 'UPDATE `syncstate` SET `confirmed_head_hash` = ?;',
    'unconfirmed_head_number': 'UPDATE `syncstate` SET `unconfirmed_head_number` = ?;',
    'unconfirmed_head_hash': 'UPDATE `syncstate` SET `unconfirmed_head_hash` = ?;'
}

ADD_CHANNEL_SQL = """
INSERT OR REPLACE INTO `channels` VALUES (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)
"""

UPDATE_CHANNEL_SQL = """
UPDATE `channels` SET
    `deposit` = ?,
    `balance` = ?,
    `last_signature` = ?,
    `settle_timeout` = ?,
    `mtime` = ?,
    `state` = ?
WHERE `sender` = ? AND `open_block_number` = ?;
"""

DEL_CHANNEL_SQL = """
DELETE FROM `channels` WHERE `sender` = ? AND `open_block_number` = ?"""


class ChannelManagerState(object):
    """The part of the channel manager state that needs to persist."""

    def __init__(self, filename):
        self.filename = filename
        self.conn = sqlite3.connect(self.filename, isolation_level="EXCLUSIVE")
        self.conn.row_factory = dict_factory
        if filename not in (None, ':memory:'):
            os.chmod(filename, 0o600)

    def setup_db(self, network_id: int, contract_address: str, receiver: str):
        """Initialize an empty database."""
        assert is_address(receiver)
        self.conn.executescript(DB_CREATION_SQL)
        self.conn.execute(UPDATE_METADATA_SQL, [network_id, contract_address, receiver])
        self.conn.commit()

    @property
    def contract_address(self):
        """The address of the channel manager contract."""
        c = self.conn.cursor()
        c.execute('SELECT `contract_address` FROM `metadata`;')
        contract_address = c.fetchone()['contract_address']
        assert c.fetchone() is None
        return contract_address

    @property
    def receiver(self):
        """The receiver address."""
        c = self.conn.cursor()
        c.execute('SELECT `receiver` FROM `metadata`;')
        receiver = c.fetchone()['receiver']
        assert c.fetchone() is None
        return receiver

    @property
    def network_id(self):
        """Network the state uses."""
        c = self.conn.cursor()
        c.execute('SELECT `network_id` FROM `metadata`;')
        network_id = c.fetchone()['network_id']
        assert c.fetchone() is None
        return network_id

    @property
    def _sync_state(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM `syncstate`;')
        state = c.fetchone()
        assert c.fetchone() is None
        assert len(state) == 4
        return state

    @property
    def confirmed_head_number(self):
        """The number of the highest processed block considered to be final."""
        return self._sync_state['confirmed_head_number']

    @confirmed_head_number.setter
    def confirmed_head_number(self, value):
        self.update_sync_state(confirmed_head_number=value)

    @property
    def confirmed_head_hash(self):
        """The hash of the highest processed block considered to be final."""
        return self._sync_state['confirmed_head_hash']

    @confirmed_head_hash.setter
    def confirmed_head_hash(self, value):
        self.update_sync_state(confirmed_head_hash=value)

    @property
    def unconfirmed_head_number(self):
        """The number of the highest processed block considered to be not yet final."""
        return self._sync_state['unconfirmed_head_number']

    @unconfirmed_head_number.setter
    def unconfirmed_head_number(self, value: int):
        self.update_sync_state(unconfirmed_head_number=value)

    @property
    def unconfirmed_head_hash(self):
        """The hash of the highest processed block considered to be not yet final."""
        return self._sync_state['unconfirmed_head_hash']

    @unconfirmed_head_hash.setter
    def unconfirmed_head_hash(self, value: int):
        self.update_sync_state(unconfirmed_head_hash=value)

    def update_sync_state(
        self,
        confirmed_head_number=None,
        confirmed_head_hash=None,
        unconfirmed_head_number=None,
        unconfirmed_head_hash=None
    ):
        """Update block numbers and hashes of confirmed and unconfirmed head."""
        if confirmed_head_number is not None:
            sql = UPDATE_SYNCSTATE_SQL['confirmed_head_number']
            self.conn.execute(sql, [confirmed_head_number])
        if confirmed_head_hash is not None:
            sql = UPDATE_SYNCSTATE_SQL['confirmed_head_hash']
            self.conn.execute(sql, [confirmed_head_hash])
        if unconfirmed_head_number is not None:
            sql = UPDATE_SYNCSTATE_SQL['unconfirmed_head_number']
            self.conn.execute(sql, [unconfirmed_head_number])
        if unconfirmed_head_hash is not None:
            sql = UPDATE_SYNCSTATE_SQL['unconfirmed_head_hash']
            self.conn.execute(sql, [unconfirmed_head_hash])
        self.conn.commit()

    @property
    def n_channels(self):
        """Returns:
            int: count of all channels, regardless of their state
        """
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) as count FROM `channels`')
        return c.fetchone()['count']

    @property
    def n_open_channels(self):
        """
        Returns:
            int: count of open channels
        """
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) as count FROM `channels` WHERE `state` = ?',
                  [ChannelState.OPEN.value])
        return c.fetchone()['count']

    def get_channels(self, confirmed=True):
        """
        Args:
            confirmed (bool, optional): return confirmed channels only. Default is True.
        Returns:
            dict: map of channels, (sender, open_block_number) => Channel
        """
        ret = dict()
        c = self.conn.cursor()
        c.execute('SELECT rowid, * FROM `channels` WHERE `confirmed` = ?', [confirmed])
        for result in c.fetchall():
            channel = self.result_to_channel(result)
            ret[result['sender'], result['open_block_number']] = channel
        return ret

    @property
    def channels(self):
        return self.get_channels(confirmed=True)

    @property
    def unconfirmed_channels(self):
        return self.get_channels(confirmed=False)

    @property
    def pending_channels(self):
        """Get list of channels in a CLOSE_PENDING state"""
        ret = dict()
        c = self.conn.cursor()
        c.execute('SELECT rowid, * FROM `channels` WHERE `state` = ?',
                  [ChannelState.CLOSE_PENDING.value])
        for result in c.fetchall():
            channel = self.result_to_channel(result)
            ret[result['sender'], result['open_block_number']] = channel
        return ret

    def result_to_channel(self, result: dict):
        """Helper function to serialize one row of `channels` table into a channel object
        """
        channel = Channel(self.receiver, result['sender'],
                          int(result['deposit']),
                          result['open_block_number'])
        channel.balance = int(result['balance'])
        channel.state = ChannelState(result['state'])
        channel.last_signature = result['last_signature']
        channel.settle_timeout = result['settle_timeout']
        channel.mtime = result['mtime']
        channel.ctime = result['ctime']
        channel.unconfirmed_topups = self.get_unconfirmed_topups(result['rowid'])
        channel.confirmed = result['confirmed']
        return channel

    def get_channel_rowid(self, sender: str, open_block_number: int):
        sender = sender
        c = self.conn.cursor()
        result = c.execute(
            'SELECT rowid from `channels` WHERE sender = ? AND open_block_number = ?',
            [sender, open_block_number]
        )
        return result.fetchone()['rowid']

    def get_unconfirmed_topups(self, channel_rowid: int):
        c = self.conn.cursor()
        c.execute('SELECT * FROM topups WHERE channel_rowid = ?', [channel_rowid])
        return {result['txhash']: result['deposit'] for result in c.fetchall()}

    def set_channel(self, channel: Channel):
        """Update channel state"""
        self.add_channel(channel)

    def channel_exists(self, sender: str, open_block_number: int):
        """Return true if channel(sender, open_block_number) exists"""
        c = self.conn.cursor()
        sql = 'SELECT 1 FROM `channels` WHERE `sender` = ? AND `open_block_number` == ?'
        c.execute(sql, [sender, open_block_number])
        result = c.fetchone()
        if result is None:
            return False
        elif result['1']:
            return True
        assert False

    def set_unconfirmed_topups(self, channel_rowid: int, topups: dict):
        assert channel_rowid is not None and isinstance(channel_rowid, int)
        self.conn.execute('DELETE FROM topups WHERE channel_rowid = ?', [channel_rowid])
        for txhash, deposit in topups.items():
            self.conn.execute('INSERT OR REPLACE INTO topups VALUES (?, ?, ?)',
                              [channel_rowid, txhash, str(deposit)])

    def add_channel(self, channel: Channel):
        """Add or update channel state"""
        assert channel.open_block_number > 0
        assert channel.state is not ChannelState.UNDEFINED
        assert is_address(channel.sender)
        params = [
            channel.sender,
            channel.open_block_number,
            str(channel.deposit),
            str(channel.balance),
            channel.last_signature,
            channel.settle_timeout,
            channel.mtime,
            channel.ctime,
            channel.state.value,
            channel.confirmed
        ]
        self.conn.execute(ADD_CHANNEL_SQL, params)
        rowid = self.get_channel_rowid(channel.sender, channel.open_block_number)
        self.set_unconfirmed_topups(rowid, channel.unconfirmed_topups)
        self.conn.commit()

    def get_channel(self, sender: str, open_block_number: int):
        assert is_address(sender)
        assert open_block_number > 0
        # TODO unconfirmed topups
        c = self.conn.cursor()
        sql = 'SELECT rowid,* FROM `channels` WHERE `sender` = ? AND `open_block_number` = ?'
        c.execute(sql, [sender, open_block_number])
        result = c.fetchone()
        assert c.fetchone() is None
        return self.result_to_channel(result)

    def del_channel(self, sender: str, open_block_number: int):
        assert is_address(sender)
        assert open_block_number > 0
        assert self.channel_exists(sender, open_block_number)
        self.conn.execute(DEL_CHANNEL_SQL, [sender, open_block_number])
        self.conn.commit()

    @classmethod
    def load(cls, filename: str, check_permissions=True):
        """Load a previously stored state."""
        assert filename and isinstance(filename, str)
        if filename != ':memory:':
            if os.path.isfile(filename) is False:
                log.error("State file  %s doesn't exist" % filename)
                return None
            if check_permissions and not check_permission_safety(filename):
                raise InsecureStateFile(filename)
        ret = cls(filename)
        log.debug("loaded saved state. head_number=%s receiver=%s" %
                  (ret.confirmed_head_number, ret.receiver))
        # for sender, block in ret.channels.keys():
        #     log.debug("loaded channel info from the saved state sender=%s open_block=%s" %
        #               (sender, block))
        return ret

    def del_unconfirmed_channels(self):
        self.conn.execute('DELETE FROM `channels` WHERE `confirmed` = 0')
        self.conn.commit()

    def set_channel_state(self, sender: str, open_block_number: int, state: ChannelState):
        assert is_address(sender)
        sender = sender
        self.conn.execute('UPDATE `channels` SET `state` = ?'
                          'WHERE `sender` = ? AND `open_block_number` = ?',
                          [state, sender, open_block_number])

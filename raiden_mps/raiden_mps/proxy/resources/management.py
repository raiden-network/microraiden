from flask_restful import Resource
import json
from collections import defaultdict

from flask_restful import reqparse

from raiden_mps.crypto import sign_close
from eth_utils import encode_hex

from raiden_mps.channel_manager import (
    NoOpenChannel
)


class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementListChannels(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementListChannels, self).__init__()
        self.channel_manager = channel_manager

    def get_all_channels(self, channel_status='all', condition=lambda k, v: True):
        return [
            {'sender_address': k[0],
             'open_block': k[1]} for k, v in
            self.channel_manager.state.channels.items()
            if (condition(k, v))]

    def get_channel_filter(self, channel_status='all'):
        if channel_status == 'open' or channel_status == 'opened':
            return lambda c: c.is_closed is False
        elif channel_status == 'closed':
            return lambda c: c.is_closed is True
        else:
            return lambda c: True

    def get(self, sender_address=None):
        parser = reqparse.RequestParser()
        parser.add_argument('status', help='block the channel was opened', default='open',
                            choices=('closed', 'opened', 'open'))
        args = parser.parse_args()
        channel_filter = self.get_channel_filter(args['status'])

        # if sender exists, return all open blocks
        if sender_address is not None:
            ret = self.get_all_channels(
                condition=lambda k, v:
                (k[0] == sender_address.lower() and
                 channel_filter(v))
            )

        # if sender is not specified, return all open channels
        else:
            channels = self.get_all_channels(condition=lambda k, v:
                                             channel_filter(v))
            joined_channels = defaultdict(list)
            for c in channels:
                joined_channels[c['sender_address']].append(c['open_block'])
            ret = [
                {'sender_address': k,
                 'blocks': v,
                 'status': args['status']} for k, v in joined_channels.items()
            ]

        return json.dumps(ret), 200

    def delete(self, sender_address):
        parser = reqparse.RequestParser()
        parser.add_argument('open_block', type=int, help='block the channel was opened')
        parser.add_argument('signature', help='last balance proof signature')
        args = parser.parse_args()
        if args.signature is None:
            return "Bad signature format", 400
        ret = sign_close(self.channel_manager.private_key, args.signature)
        return ret, 200


class ChannelManagementChannelInfo(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementChannelInfo, self).__init__()
        self.channel_manager = channel_manager

    def get(self, sender_address, opening_block):
        try:
            key = (sender_address.lower(), opening_block)
            sender_channel = self.channel_manager.state.channels[key]
        except KeyError:
            return "Sender address not found", 404

        return sender_channel.toJSON(), 200

    def delete(self, sender_address, opening_block):
        parser = reqparse.RequestParser()
        parser.add_argument('signature', help='last balance proof signature')
        args = parser.parse_args()
        if args.signature is None:
            return "Bad signature format", 400

        try:
            close_signature = self.channel_manager.sign_close(
                sender_address,
                opening_block,
                args.signature)
        except NoOpenChannel as e:
            return str(e), 400
        except KeyError:
            return "Channel not found", 404
        ret = {'close_signature': encode_hex(close_signature)}

        return json.dumps(ret), 200


class ChannelManagementAdmin(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementAdmin, self).__init__()
        self.channel_manager = channel_manager

    def get(self):
        return "OK"

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('open_block', type=int, help='block the channel was opened')
        parser.add_argument('sender')
        args = parser.parse_args()
        self.channel_manager.close_channel(args.sender.lower(), args.open_block)

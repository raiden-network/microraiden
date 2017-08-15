from flask_restful import Resource
import json

from flask_restful import reqparse


class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementListChannels(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementListChannels, self).__init__()
        self.channel_manager = channel_manager

    def get(self, sender_address=None):
        x = self.channel_manager.state.channels
        # if sender exists, return all open blocks
        if sender_address is not None:
            ret = [k[1] for k, v in x.items() if
                   (k[0] == sender_address.lower() and
                   v.is_closed is False)]
        # if sender is not specified, return all open channels
        else:
            ret = {}
            for k, v in x.items():
                if v.is_closed is True:
                    continue
                if k[0] in ret:
                    ret[k[0]].append(k[1])
                else:
                    ret[k[0]] = [k[1]]

        return json.dumps(ret), 200

    def delete(self, sender_address):
        parser = reqparse.RequestParser()
        parser.add_argument('open_block', type=int, help='block the channel was opened')
        parser.add_argument('signature', help='last balance proof signature')
        args = parser.parse_args()
        if args.signature is None:
            return "Bad signature format", 400
        ret = self.channel_manager.sign_close(args.sender, args.open_block, args.signature)
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

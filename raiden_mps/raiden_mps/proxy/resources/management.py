from flask_restful import Resource
import json

from flask_restful import reqparse




class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementChannels(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementChannels, self).__init__()
        self.channel_manager = channel_manager

    def get(self, sender_address):
        x = self.channel_manager.state.channels
        block_opens = [k[1] for k, v in x.items() if k[0] == sender_address.lower()]

        return json.dumps(block_opens), 200

    def delete(self, sender_address):
        parser = reqparse.RequestParser()
        parser.add_argument('open_block', type=int, help='block the channel was opened')
        parser.add_argument('signature', help='last balance proof signature')
        args = parser.parse_args()
        if args.signature is None:
            return "Bad signature format", 400
        ret = self.channel_manager.sign_close(args.sender, args.open_block, args.signature)
        return ret, 200


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

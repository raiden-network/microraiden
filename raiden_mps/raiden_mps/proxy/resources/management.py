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

    def get(self, channel_id):
        import pudb; pudb.set_trace()
        x = self.channel_manager.state.channels
        ret = {}
        for k, v in x.items():
            ret[k[0]] = {}
        for k, v in x.items():
            ret[k[0]][k[1]] = str(v)

        return json.dumps(ret), 200

    def delete(self, channel_id):
        parser = reqparse.RequestParser()
        parser.add_argument('sender', type=str, help='counterparty')
        parser.add_argument('open_block', type=int, help='block the channel was opened')
        parser.add_argument('signature', help='last balance proof signature')
        args = parser.parse_args()
        ret = self.channel_manager.sign_close(args.sender, args.open_block, args.signature)
        return ret, 200



class ChannelManagementAdmin(Resource):
    def get(self):
        return "OK"

from flask_restful import Resource
import json


class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementChannels(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementChannels, self).__init__()
        self.channel_manager = channel_manager

    def get(self, channel_id):
        x = self.channel_manager.state.channels
        ret = {}
        for k, v in x.items():
            ret[k[0]] = {}
        for k, v in x.items():
            ret[k[0]][k[1]] = str(v)

        return json.dumps(ret[channel_id]), 200



class ChannelManagementAdmin(Resource):
    def get(self):
        return "OK"

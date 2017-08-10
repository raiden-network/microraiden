from flask_restful import Resource
import json


class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementChannels(Resource):
    def __init__(self, channel_manager):
        super(ChannelManagementChannels, self).__init__()
        self.channel_manager = channel_manager

    def get(self, id):
        return 200, json.dumps(self.channel_manager.state.channels)



class ChannelManagementAdmin(Resource):
    def get(self):
        return "OK"

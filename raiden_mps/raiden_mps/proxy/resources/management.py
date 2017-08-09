from flask_restful import Resource


class ChannelManagementRoot(Resource):
    def get(self):
        return "OK"


class ChannelManagementClose(Resource):
    def get(self):
        return "OK"

    def post(self):
        return ""


class ChannelManagementAdmin(Resource):
    def get(self):
        return "OK"

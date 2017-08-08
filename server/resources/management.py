from flask_restful import Resource


class ChannelManagementRoot(Resource):
    def get(self):
        return 200, "OK"


class ChannelManagementClose(Resource):
    def get(self):
        return 200, "OK /close"

    def post(self):
        return 200


class ChannelManagementAdmin(Resource):
    def get(self):
        return 200, "OK /admin"

from flask_restful import (
    Resource
)
from flask import make_response


class StaticFilesServer(Resource):
    def __init__(self, directory):
        super(StaticFilesServer, self).__init__()
        self.directory = directory

    def get(self, content):
        try:
            content.index("/")
            return "", 403
        except ValueError:
            pass
        data = open(self.directory + "/" + content).read()
        return make_response(data, 200, {'Content-Type' : 'application/javascript'})

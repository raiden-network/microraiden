import time
import uuid
from flask_httpauth import HTTPBasicAuth
from flask import g
from flask_restful import Resource

auth = HTTPBasicAuth()


class TokenAccess:
    def __init__(self, user: str):
        self.token = str(uuid.uuid1())
        self.time_created = time.time()
        self.time_accessed = time.time()
        self.user = user


class UsersDB:
    def __init__(self):
        self.users = {}
        self.tokens = {}
        self.token_expiry_seconds = 600  # token is valid for 10 minutes

    def add_user(self, user: str, password: str):
        self.users[user] = password

    def del_user(self, user: str):
        self.users.pop(user)

    def authorize(self, user_or_token: str, password: str):
        """Authorize user using token or username/password combination"""
        g.user = user_or_token
        token_record = self.verify_token(user_or_token)
        if token_record is not None:
            token_record.time_accessed = time.time()
            return True
        else:
            self.tokens.pop(user_or_token, '')
        if user_or_token not in self.users:
            return False
        return self.users[user_or_token] == password

    def verify_token(self, token: str):
        """Verify if the token is valid and not expired"""
        token_record = self.tokens.get(token, None)
        if token_record is None:
            return None
        t_diff = time.time() - token_record.time_accessed
        assert t_diff >= 0
        if t_diff > self.token_expiry_seconds:
            return None
        return token_record

    def remove_token(self, token: str):
        del self.tokens[token]

    def get_token(self, user: str):
        token_record = TokenAccess(user)
        self.tokens[token_record.token] = token_record
        return token_record.token


userDB = UsersDB()


# used by flask to process http auth requests
@auth.verify_password
def verify_password(username, password):
    return userDB.authorize(username, password)


# two resources for managing the login
# exported as /login and /logout
class ChannelManagementLogin(Resource):
    @auth.login_required
    def get(self):
        token = userDB.get_token(g.user)
        return {'token': token}, 200


class ChannelManagementLogout(Resource):
    @auth.login_required
    def get(self):
        userDB.remove_token(g.user)
        return "OK", 200

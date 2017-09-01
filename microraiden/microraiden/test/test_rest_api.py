import pytest # noqa
import requests
import json
import gevent

from microraiden.config import API_PATH


def test_resources(doggo_proxy, api_endpoint_address, users_db):
    auth_credentials = ('user', 'password')
    users_db.add_user(auth_credentials[0], auth_credentials[1])
    users_db.token_expiry_seconds = 0.5
    api_path = "http://" + api_endpoint_address + API_PATH

    # without auth, refuse access
    rv = requests.get(api_path + "/admin")
    assert rv.status_code == 401

    #  bad login
    rv = requests.get(api_path + "/login", auth=('user', 'bad_password'))
    assert rv.status_code == 401

    # good login, we got the token
    rv = requests.get(api_path + "/login", auth=auth_credentials)
    assert rv.status_code == 200
    json_response = json.loads(rv.text)
    assert 'token' in json_response

    token_credentials = (json_response['token'], '')
    # use the token to login
    rv = requests.get(api_path + "/admin", auth=token_credentials)
    assert rv.status_code == 200

    # logout with an invalid token
    rv = requests.get(api_path + "/logout", auth=('invalid_token', ''))
    assert rv.status_code == 401

    # logout with a valid token
    rv = requests.get(api_path + "/logout", auth=token_credentials)
    assert rv.status_code == 200

    # after logout, refuse access
    rv = requests.get(api_path + "/admin", auth=token_credentials)
    assert rv.status_code == 401

    # TODO: test token expiration. we must set token expiry timeout somehow
    # login again
    rv = requests.get(api_path + "/login", auth=auth_credentials)
    assert rv.status_code == 200
    json_response = json.loads(rv.text)
    assert 'token' in json_response

    token_credentials = (json_response['token'], '')
    gevent.sleep(1)

    # use the token to login
    rv = requests.get(api_path + "/admin", auth=token_credentials)
    assert rv.status_code == 401

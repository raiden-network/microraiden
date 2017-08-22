import pytest # noqa

from raiden_mps.config import API_PATH


def test_resources(doggo_proxy):
    app = doggo_proxy.app
    tc = app.test_client()

    rv = tc.get("/nonexisting-doggo.jpg")
    assert rv.status_code == 404

    rv = tc.get("/doggo.jpg")
    assert rv.status_code == 402

    rv = tc.get(API_PATH + "/channels/")
    assert rv.status_code == 200

    rv = tc.get(API_PATH + "/admin")
    assert rv.status_code == 200

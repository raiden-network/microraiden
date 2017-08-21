import pytest # noqa


def test_resources(doggo_proxy):
    app = doggo_proxy.app
    tc = app.test_client()

    rv = tc.get("/nonexisting-doggo.jpg")
    assert rv.status_code == 404

    rv = tc.get("/doggo.jpg")
    assert rv.status_code == 402

    rv = tc.get("/cm")
    assert rv.status_code == 200

    rv = tc.get("/cm/channels/")
    assert rv.status_code == 200

    rv = tc.get("/cm/admin")
    assert rv.status_code == 200

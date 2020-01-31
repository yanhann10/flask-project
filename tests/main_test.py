import run


def test_index():
    run.app.testing = True
    client = run.app.test_client()

    r = client.get('/')
    assert r.status_code == 200

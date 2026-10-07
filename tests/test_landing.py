def test_logged_out_root_shows_landing_page(client):
    resp = client.get("/")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Development Mode" in body
    assert "Log in with Spotify" in body
    assert 'href="https://github.com/d4ny41/boomba" target="_blank" rel="noopener noreferrer"' in body
    assert 'href="https://github.com/d4ny41/boomba#demo" target="_blank" rel="noopener noreferrer"' in body


def test_logged_in_root_redirects_to_feed(client, make_user, login_as):
    login_as(make_user("Alice"))

    resp = client.get("/")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/feed")

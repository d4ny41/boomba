from datetime import datetime

import pytest

from app.models import Friendship, Track, db


def befriend(a, b):
    db.session.add(Friendship(user_id=a.id, friend_id=b.id, status="accepted"))
    db.session.commit()


@pytest.fixture
def alice(make_user):
    return make_user("Alice")


@pytest.fixture
def bob(make_user):
    return make_user("Bob")


@pytest.fixture
def carol(make_user):
    return make_user("Carol")


def test_request_to_self_is_rejected(client, login_as, alice):
    login_as(alice)
    resp = client.post(f"/friends/request/{alice.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"send a friend request to yourself" in resp.data
    assert Friendship.query.count() == 0


def test_duplicate_request_creates_one_row(client, login_as, alice, bob):
    login_as(alice)
    client.post(f"/friends/request/{bob.id}")
    client.post(f"/friends/request/{bob.id}")

    rows = Friendship.query.all()
    assert len(rows) == 1
    assert (rows[0].user_id, rows[0].friend_id, rows[0].status) == (alice.id, bob.id, "pending")


def test_reverse_request_accepts_existing(client, login_as, alice, bob):
    login_as(alice)
    client.post(f"/friends/request/{bob.id}")
    login_as(bob)
    client.post(f"/friends/request/{alice.id}")

    rows = Friendship.query.all()
    assert len(rows) == 1
    assert (rows[0].user_id, rows[0].friend_id, rows[0].status) == (alice.id, bob.id, "accepted")


@pytest.mark.parametrize("action", ["accept", "decline"])
@pytest.mark.parametrize("who", ["sender", "third_party"])
def test_only_recipient_can_respond(client, login_as, alice, bob, carol, action, who):
    login_as(alice)
    client.post(f"/friends/request/{bob.id}")
    request_id = Friendship.query.one().id

    login_as(alice if who == "sender" else carol)
    resp = client.post(f"/friends/{action}/{request_id}")
    assert resp.status_code == 404

    row = Friendship.query.one()
    assert row.status == "pending"


@pytest.mark.parametrize("action,expected", [("accept", "accepted"), ("decline", None)])
def test_recipient_can_respond(client, login_as, alice, bob, action, expected):
    login_as(alice)
    client.post(f"/friends/request/{bob.id}")
    request_id = Friendship.query.one().id

    login_as(bob)
    resp = client.post(f"/friends/{action}/{request_id}")
    assert resp.status_code == 302

    row = Friendship.query.first()
    assert (row.status if row else None) == expected


@pytest.fixture(autouse=True)
def no_spotify(monkeypatch):
    """Fail loudly if any view under test tries to reach Spotify."""

    def boom(*args, **kwargs):
        raise AssertionError("Spotify API must not be called")

    monkeypatch.setattr("app.routes.get_spotify_for_user", boom)
    monkeypatch.setattr("app.routes.get_oauth", boom)


def test_ratings_page_404_for_non_friend(client, login_as, alice, bob, make_rating):
    make_rating(bob, "Secret Song", 5)
    login_as(alice)
    assert client.get(f"/friends/{bob.id}/ratings").status_code == 404


def test_ratings_page_404_for_pending_request(client, login_as, alice, bob):
    login_as(alice)
    client.post(f"/friends/request/{bob.id}")
    assert client.get(f"/friends/{bob.id}/ratings").status_code == 404


def test_ratings_page_404_for_nonexistent_user(client, login_as, alice):
    login_as(alice)
    assert client.get("/friends/9999/ratings").status_code == 404


def test_ratings_page_for_self_redirects_to_rate(client, login_as, alice):
    login_as(alice)
    resp = client.get(f"/friends/{alice.id}/ratings")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/rate")


def test_ratings_page_requires_login(client, bob):
    resp = client.get(f"/friends/{bob.id}/ratings")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_friend_sees_ratings(client, login_as, alice, bob, make_rating):
    befriend(alice, bob)
    shared = make_rating(bob, "Shared Song", 3)
    make_rating(alice, None, 4, track=db.session.get(Track, shared.track_id))
    make_rating(bob, "Older Five", 5, rated_at=datetime(2026, 1, 1))
    make_rating(bob, "Newer Five", 5, rated_at=datetime(2026, 3, 1))
    make_rating(bob, "Low Song", 1)
    make_rating(alice, "Alice Only", 2)

    login_as(alice)
    resp = client.get(f"/friends/{bob.id}/ratings")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert "<h1>Bob's ratings</h1>" in body
    # Score descending, then most recent first within a score.
    names = ["Newer Five", "Older Five", "Shared Song", "Low Song"]
    positions = [body.index(n) for n in names]
    assert positions == sorted(positions)
    assert "Alice Only" not in body

    shared_item = body[body.index("Shared Song"):body.index("Low Song")]
    assert "Their rating: 3/5" in shared_item
    assert "Your rating: 4/5" in shared_item
    low_item = body[body.index("Low Song"):]
    assert "Their rating: 1/5" in low_item
    assert "Your rating: &mdash;" in low_item


def test_ratings_page_404_after_unfriending(client, login_as, alice, bob, make_rating):
    befriend(alice, bob)
    make_rating(bob, "Some Song", 4)
    login_as(alice)
    assert client.get(f"/friends/{bob.id}/ratings").status_code == 200

    resp = client.post(f"/friends/remove/{bob.id}")
    assert resp.status_code == 302
    assert Friendship.query.count() == 0

    assert client.get(f"/friends/{bob.id}/ratings").status_code == 404

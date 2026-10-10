from datetime import datetime

import pytest

from app.models import Rating, Track, db


@pytest.fixture
def alice(make_user):
    return make_user("Alice")


@pytest.fixture
def track(app):
    track = Track(spotify_track_id="track-1", name="Some Song", artist_name="Some Artist")
    db.session.add(track)
    db.session.commit()
    return track


def rate(client, track_id, score, next="rate"):
    return client.post("/rate", data={"track_id": track_id, "score": score, "next": next})


def test_first_rating_creates_one_row(client, login_as, alice, track):
    login_as(alice)
    resp = rate(client, track.id, "4")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/rate#track-{track.id}")

    rating = Rating.query.one()
    assert (rating.user_id, rating.track_id, rating.score) == (alice.id, track.id, 4)


def test_rerating_updates_same_row(client, login_as, alice, track, make_rating):
    original = make_rating(alice, None, 2, rated_at=datetime(2026, 1, 1), track=track)
    login_as(alice)
    rate(client, track.id, "5")

    rating = Rating.query.one()
    assert rating.id == original.id
    assert rating.score == 5
    assert rating.rated_at > datetime(2026, 1, 1)


@pytest.mark.parametrize("score", ["0", "6", "abc"])
def test_invalid_score_rejected(client, login_as, alice, track, score):
    login_as(alice)
    resp = rate(client, track.id, score)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/rate")
    assert Rating.query.count() == 0


def test_nonexistent_track_rejected(client, login_as, alice, track):
    login_as(alice)
    resp = rate(client, track.id + 999, "3", next="feed")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/feed")
    assert Rating.query.count() == 0


@pytest.mark.parametrize("next", ["https://evil.example", "/friends", ""])
def test_unknown_next_falls_back_to_rate(client, login_as, alice, track, next):
    login_as(alice)
    resp = rate(client, track.id, "3", next=next)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/rate#track-{track.id}")
    assert Rating.query.one().score == 3

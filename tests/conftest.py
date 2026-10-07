import itertools
from datetime import datetime

import pytest

from app import create_app
from app.models import Rating, Track, User, db


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            # Flask-SQLAlchemy shares one connection for in-memory SQLite, so each test gets a fresh DB.
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    counter = itertools.count(1)

    def _make_user(display_name):
        n = next(counter)
        user = User(
            spotify_id=f"spotify-{n}",
            display_name=display_name,
            spotify_refresh_token=f"refresh-{n}",
        )
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user


@pytest.fixture
def login_as(client):
    def _login_as(user):
        with client.session_transaction() as s:
            s["user_id"] = user.id

    return _login_as


@pytest.fixture
def make_rating(app):
    counter = itertools.count(1)

    def _make_rating(user, track_name, score, rated_at=None, track=None):
        if track is None:
            track = Track(
                spotify_track_id=f"track-{next(counter)}",
                name=track_name,
                artist_name=f"{track_name} Artist",
            )
            db.session.add(track)
            db.session.flush()
        rating = Rating(
            user_id=user.id,
            track_id=track.id,
            score=score,
            rated_at=rated_at or datetime(2026, 1, 1),
        )
        db.session.add(rating)
        db.session.commit()
        return rating

    return _make_rating

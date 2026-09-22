from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spotify_id = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    profile_image_url = db.Column(db.String(512), nullable=True)
    spotify_refresh_token = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), default=func.now())


class Track(db.Model):
    __tablename__ = "tracks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spotify_track_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    artist_name = db.Column(db.String(256), nullable=False)
    album_name = db.Column(db.String(256), nullable=True)
    album_art_url = db.Column(db.String(512), nullable=True)
    cached_at = db.Column(db.DateTime, server_default=func.now(), default=func.now())


class Rating(db.Model):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_ratings_user_track"),
        CheckConstraint("score BETWEEN 1 AND 5", name="ck_ratings_score_range"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey("tracks.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        default=func.now(),
        onupdate=func.now(),
    )


class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(16), nullable=False)  # 'pending' / 'accepted'
    created_at = db.Column(db.DateTime, server_default=func.now(), default=func.now())

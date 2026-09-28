from sqlalchemy import and_, or_

from app.models import Friendship, Track, User, db

TARGET_ART_WIDTH = 300


def _pick_album_art(images):
    if not images:
        return None
    sized = [img for img in images if img.get("width")]
    if not sized:
        return images[0]["url"]
    return min(sized, key=lambda img: abs(img["width"] - TARGET_ART_WIDTH))["url"]


def _track_from_dict(track_dict):
    album = track_dict.get("album") or {}
    return Track(
        spotify_track_id=track_dict["id"],
        name=track_dict["name"],
        artist_name=", ".join(a["name"] for a in track_dict.get("artists") or []),
        album_name=album.get("name"),
        album_art_url=_pick_album_art(album.get("images") or []),
    )


def get_or_create_tracks(track_dicts):
    """Return Track rows for raw Spotify track objects, inserting missing ones.

    Commits once for the whole batch. Tracks without an id (local files) are
    skipped; repeated ids are returned once, in first-seen order.
    """
    unique = {}
    for track_dict in track_dicts:
        if track_dict and track_dict.get("id"):
            unique.setdefault(track_dict["id"], track_dict)
    if not unique:
        return []

    existing = {
        t.spotify_track_id: t
        for t in Track.query.filter(Track.spotify_track_id.in_(unique)).all()
    }
    new_tracks = [
        _track_from_dict(d) for sid, d in unique.items() if sid not in existing
    ]
    if new_tracks:
        db.session.add_all(new_tracks)
        db.session.commit()
        existing.update((t.spotify_track_id, t) for t in new_tracks)

    return [existing[sid] for sid in unique]


def get_or_create_track(track_dict):
    """Return the Track row for one raw Spotify track object, inserting if needed."""
    tracks = get_or_create_tracks([track_dict])
    return tracks[0] if tracks else None


def _between(user_a_id, user_b_id):
    """Filter clause matching a Friendship row between two users, either direction."""
    return or_(
        and_(Friendship.user_id == user_a_id, Friendship.friend_id == user_b_id),
        and_(Friendship.user_id == user_b_id, Friendship.friend_id == user_a_id),
    )


def get_relationship(user_a_id, user_b_id):
    """Return the Friendship row between two users (any status, either direction), or None."""
    return Friendship.query.filter(_between(user_a_id, user_b_id)).first()


def get_friendship(user_a_id, user_b_id):
    """Return the accepted Friendship row between two users, or None."""
    return Friendship.query.filter(
        _between(user_a_id, user_b_id), Friendship.status == "accepted"
    ).first()


def are_friends(user_a_id, user_b_id):
    return get_friendship(user_a_id, user_b_id) is not None


def get_friends(user_id):
    """Return the User rows this user has an accepted friendship with, by name."""
    rows = Friendship.query.filter(
        or_(Friendship.user_id == user_id, Friendship.friend_id == user_id),
        Friendship.status == "accepted",
    ).all()
    ids = {r.friend_id if r.user_id == user_id else r.user_id for r in rows}
    if not ids:
        return []
    return User.query.filter(User.id.in_(ids)).order_by(User.display_name).all()


def count_incoming_requests(user_id):
    return Friendship.query.filter_by(friend_id=user_id, status="pending").count()

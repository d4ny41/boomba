from app.models import Track, db

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

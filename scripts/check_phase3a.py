"""Phase 3a check: cache the first user's recently played tracks.

Run from the project root: venv/bin/python scripts/check_phase3a.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.models import User, db
from app.services import get_or_create_tracks
from app.spotify_client import SpotifyAuthError, get_spotify_for_user


def track_count():
    return db.session.execute(text("SELECT COUNT(*) FROM tracks")).scalar()


app = create_app()

with app.app_context():
    user = User.query.order_by(User.id).first()
    if user is None:
        sys.exit("No users in the users table; log in via /login first.")
    print(f"User: {user.display_name} ({user.spotify_id})")
    print(f"tracks before: {track_count()}")

    try:
        sp = get_spotify_for_user(user)
    except SpotifyAuthError as e:
        sys.exit(f"Re-login required: {e}")

    items = sp.current_user_recently_played(limit=20)["items"]
    seen = set()
    raw_tracks = []
    for item in items:
        track = item.get("track")
        if track and track.get("id") and track["id"] not in seen:
            seen.add(track["id"])
            raw_tracks.append(track)
    print(f"recently played: {len(items)} items, {len(raw_tracks)} unique tracks\n")

    for t in get_or_create_tracks(raw_tracks):
        art = "yes" if t.album_art_url else "no"
        print(f"  [{t.id}] {t.name} — {t.artist_name} — art: {art}")

    print(f"\nSELECT COUNT(*) FROM tracks -> {track_count()}")

import spotipy
from flask import current_app
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.exceptions import SpotifyOauthError
from spotipy.oauth2 import SpotifyOAuth

from app.models import db

SCOPE = "user-top-read user-read-recently-played"


class SpotifyAuthError(Exception):
    """The user's stored refresh token no longer works; they must log in again."""


def get_oauth():
    # Not cache_handler=None: that falls back to spotipy's on-disk cache, shared across users.
    return SpotifyOAuth(
        client_id=current_app.config["SPOTIFY_CLIENT_ID"],
        client_secret=current_app.config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=current_app.config["SPOTIFY_REDIRECT_URI"],
        scope=SCOPE,
        cache_handler=MemoryCacheHandler(),
        show_dialog=True,
    )


def get_spotify_for_user(user):
    """Raises SpotifyAuthError if the stored refresh token is rejected; send the user to /login."""
    try:
        token_info = get_oauth().refresh_access_token(user.spotify_refresh_token)
    except SpotifyOauthError as e:
        raise SpotifyAuthError(
            f"Spotify refresh failed for user {user.id}: {e.error or e}"
        ) from e

    # Spotify can rotate the refresh token, after which the old one stops working.
    new_refresh_token = token_info.get("refresh_token")
    if new_refresh_token and new_refresh_token != user.spotify_refresh_token:
        user.spotify_refresh_token = new_refresh_token
        db.session.commit()

    return spotipy.Spotify(auth=token_info["access_token"])

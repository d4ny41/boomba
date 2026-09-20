from flask import current_app
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth

SCOPE = "user-top-read user-read-recently-played"


def get_oauth():
    # MemoryCacheHandler() is required: cache_handler=None makes spotipy fall back
    # to its default file cache, which is shared on disk and would cross sessions
    # between users. See CLAUDE.md.
    return SpotifyOAuth(
        client_id=current_app.config["SPOTIFY_CLIENT_ID"],
        client_secret=current_app.config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=current_app.config["SPOTIFY_REDIRECT_URI"],
        scope=SCOPE,
        cache_handler=MemoryCacheHandler(),
        show_dialog=True,
    )

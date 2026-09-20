# boomba

"boomba" is the actual project name (and project root directory), not a placeholder from any reference docs.

## Stack

- Flask
- spotipy (Spotify Web API)
- MySQL via Flask-SQLAlchemy with the pymysql driver
- Jinja2 templates
- Docker for local MySQL (not yet started)

## Environment

- `venv/` already exists at the project root and is listed in `.gitignore` alongside `.env` and `__pycache__/`. Do not recreate or touch these.
- `.env` is already populated with `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, and `FLASK_SECRET_KEY`. Read from it; never regenerate or overwrite these values.

## Auth model

Sign in with Spotify only. There is no password system.

**CRITICAL:** when constructing `SpotifyOAuth` in `app/spotify_client.py`, explicitly pass `cache_handler=MemoryCacheHandler()` (imported from `spotipy.cache_handler`). Do NOT pass `cache_handler=None`: spotipy treats `None` as "no handler provided" and falls back to its default file-based `CacheFileHandler`, which writes a `.cache` file. Do not let spotipy fall back to its default file-based token cache under any circumstance. That cache is shared on disk and causes session crossover between users.

Refresh tokens are stored per-user in the database instead (to be added once models exist).

## Project structure

These files and directories already exist as empty scaffolding. Do not recreate the file structure; only populate them going forward:

- `app/__init__.py`
- `app/config.py`
- `app/models.py`
- `app/routes.py`
- `app/spotify_client.py`
- `run.py`
- `templates/`
- `static/`

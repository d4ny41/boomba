# Boomba

Boomba is a Flask web app where you sign in with Spotify, rate the tracks you've been listening to on a 1 to 5 scale, and see how your friends rated theirs. I built it as a solo project to practise OAuth, relational schema design and web security against a real third-party API with real platform constraints.

## Demo

Demo video coming soon.

Live: RENDER_URL_HERE. Sign-in only works for Spotify accounts on the app's allowlist (see [Known limitations](#known-limitations)), and the free host may take a moment to wake up.

## Features

- Sign in with Spotify. There are no passwords.
- Feed: your 20 top tracks from the last four weeks, with album art, rated inline.
- Rate page: your 50 most recent plays, deduplicated, each with a 1 to 5 rating. Re-rating a track updates your existing score.
- Friends: send, accept, decline and cancel friend requests, and remove friends. The people you can add are other Boomba users, not Spotify's user directory.
- Friend ratings: view an accepted friend's rated tracks, highest score first, next to your own score for the same track.

## Tech stack

- Python 3, Flask 3, Jinja2 templates
- spotipy for the Spotify Web API
- MySQL 8 via Flask-SQLAlchemy / SQLAlchemy 2 and the PyMySQL driver
- Flask-WTF for CSRF protection
- gunicorn for production
- pytest
- Docker for local MySQL

## How it works

**Authentication.** `/login` redirects to Spotify's authorisation page with a random `state` value stored in the session, and `/callback` checks that value before exchanging the code for tokens. The app then calls `GET /me`, creates or updates the matching row in `users`, and stores that user's Spotify refresh token on the row. On each request that needs Spotify data, the stored refresh token is exchanged for a fresh access token; if Spotify rotates the refresh token, the new one is saved. If the refresh token has been revoked, the session is cleared and the user is sent back to log in.

spotipy's `SpotifyOAuth` writes tokens to a `.cache` file on disk by default, and passing `cache_handler=None` still falls back to that file. A single file shared by every user of the server would let one user's token be picked up by another user's request. `app/spotify_client.py` passes `MemoryCacheHandler()` explicitly, so spotipy never touches disk, and the database is the only place tokens persist.

**Track caching.** Track metadata from Spotify (name, artists, album, album art) is stored in a `tracks` table keyed on the Spotify track ID. Each page load looks up all the tracks it received in one query and inserts only the missing ones in a single commit. The friend ratings page reads only from the database and makes no Spotify calls.

**Schema.** Four tables:

| Table | Purpose | Constraints |
|---|---|---|
| `users` | One row per Spotify account, with its refresh token | `spotify_id` unique |
| `tracks` | Cached Spotify track metadata | `spotify_track_id` unique |
| `ratings` | A user's 1 to 5 score for a track | Unique on (`user_id`, `track_id`); check `score BETWEEN 1 AND 5` |
| `friendships` | A friend request from `user_id` to `friend_id`, with status `pending` or `accepted` | Foreign keys to `users` |

The unique constraint on `ratings` lets a rating be saved with a single `INSERT ... ON DUPLICATE KEY UPDATE` statement, so a user has at most one score per track.

## Security

- **CSRF.** Rating and all friend actions are POST routes protected by Flask-WTF's `CSRFProtect`, and every form includes a CSRF token. A failed check redirects back to the referring page only if it is on the same host, to avoid an open redirect.
- **Session cookies.** `SameSite=Lax` and `HttpOnly` are always set. When `APP_ENV=production`, `Secure` is also set and debug mode is forced off.
- **Rating validation.** The server accepts only the strings `"1"` to `"5"` as a score and only an existing track ID; anything else is rejected without writing. The page to return to after rating comes from a fixed allowlist, not from a URL in the form. The database check constraint on `score` is a second line of defence.
- **Friendship authorisation (IDOR).** `/friends/<user_id>/ratings` checks for an accepted friendship between the logged-in user and `user_id` before loading anything, and returns 404, not 403, to non-friends so the response doesn't reveal whether that user exists. Accept, decline, cancel and remove apply the same pattern: a request ID or user ID that doesn't belong to the current user returns 404.
- **OAuth state.** The `state` parameter is checked on callback to block login CSRF.

## Running locally

### Prerequisites

- Python 3 (developed on 3.13)
- Docker
- A Spotify account and a Spotify app of your own (below)

### 1. Register a Spotify app

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Add the redirect URI `http://127.0.0.1:5000/callback` exactly. Use `127.0.0.1`, not `localhost`.
3. Copy the client ID and client secret.
4. Under User Management, add the Spotify account email of everyone who will log in, including yourself. Accounts that aren't listed get a 403 from Spotify.

### 2. Start MySQL

```
docker run --name boomba-db \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=boomba \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_app_password \
  -p 3306:3306 \
  -d mysql:8
```

### 3. Configure environment

```
cp .env.example .env
```

Fill in the Spotify client ID, secret and redirect URI, a `FLASK_SECRET_KEY` (generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`), and the MySQL values matching the Docker command above. Leave `MYSQL_SSL_CA` empty for local Docker MySQL. The app refuses to start if any required variable is missing. Each variable is described in `.env.example`.

### 4. Install dependencies and create the tables

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

`init_db.py` creates the four tables. It takes `--env-file` to target a different database, for example `python init_db.py --env-file .env.production`.

### 5. Run

```
python run.py
```

Open http://127.0.0.1:5000. Set `FLASK_DEBUG=1` in `.env` to enable the debugger and reloader. In production, set `APP_ENV=production` and serve `run:app` with gunicorn.

## Running tests

```
pytest
```

The tests run against an isolated in-memory SQLite database created fresh for each test, so MySQL doesn't need to be running and no Spotify calls are made. A populated `.env` is still required, because the config checks for every required variable on import. There are currently 18 tests, covering the landing page, the friend request flow, and friend ratings authorisation.

## Known limitations

- **Spotify Development Mode.** This is a Spotify platform constraint, not a bug. Apps in Development Mode are limited to 5 allowlisted users, the app owner's account needs Spotify Premium, and many endpoints are restricted, including reading Spotify-curated playlists such as the global charts. Lifting these limits (Extended Quota Mode) requires an established business with a large existing user base, which isn't reachable for a project like this. The app is designed around it: the feed uses each user's own top tracks instead of a global chart, and friends are found from Boomba's own `users` table instead of Spotify's user directory.
- **Token refresh on every request.** Access tokens are not stored; each request that calls Spotify refreshes one from the stored refresh token. This is a deliberate simplification that costs one extra Spotify call per page load.
- **Cold starts.** The live demo runs on a free hosting tier that sleeps when idle, so the first request after a quiet period is slow.

## Roadmap

- Track search, so you can rate tracks outside your recent plays and top tracks
- A combined feed of ratings across your friend group
- Written reviews and comments on ratings

## License

MIT. See [LICENSE](LICENSE).

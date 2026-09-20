# Phase 1 — Environment and Spotify OAuth Setup

**Goal of this phase:** a Flask app where you can click "Log in with Spotify," authorize, land back on your app logged in, and see a new row appear in MySQL. Nothing else. Get this rock-solid before touching the rating or feed features.

## Step 1 — Prerequisites

Confirm you have, before writing any project code:
- Python 3.10+ installed
- Docker installed (for MySQL — covered fully in Phase 2, but pull the image now if you want: `docker pull mysql:8`)
- A Spotify account for yourself with an active Premium subscription (required for the app owner specifically — your test users do not need Premium)
- Git initialized in your project folder, with a `.gitignore` that excludes `.env`, `__pycache__/`, and any virtual environment folder, before you write a single line of application code

## Step 2 — Register the app on the Spotify Developer Dashboard

1. Go to the Spotify Developer Dashboard and log in with the account that will be the app owner.
2. Click "Create app."
3. Name it, give it a short description.
4. Set the Redirect URI to exactly `http://127.0.0.1:5000/callback` — this string must match character-for-character what your Flask route listens on later. A trailing slash mismatch will break the flow.
5. When asked which API/SDK you're integrating with, select the Web API.
6. Agree to the terms and create the app.

## Step 3 — Save your credentials

On the app's settings page, copy the **Client ID**, and click "View client secret" to reveal and copy the **Client Secret**. Put both in your `.env` file immediately:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=generate_a_long_random_string_here
```

Never hardcode these in a `.py` file, even temporarily "just to test."

## Step 4 — Allowlist your test users

Still in the Dashboard, under User Management for this app, add the Spotify account email addresses of yourself and anyone else you want testing this over the weekend (up to 5 total, owner included). Do this now — an account that isn't allowlisted will fail authentication with a 403 that looks like a bug in your code but isn't.

## Step 5 — Project skeleton

Create the following structure before writing logic:

```
spotify-rating-app/
  app/
    __init__.py         (Flask app factory, loads config)
    config.py           (reads all env vars from .env)
    models.py           (SQLAlchemy models — built in Phase 2)
    routes.py           (login/callback/logout now, rating/feed later)
    spotify_client.py   (spotipy OAuth setup and helper functions)
  templates/
  static/
  .env
  .gitignore
  requirements.txt
  run.py                (entry point)
```

## Step 6 — Install dependencies

```
pip install flask spotipy flask-sqlalchemy pymysql python-dotenv
pip freeze > requirements.txt
```

## Step 7 — Configure the spotipy OAuth object

In `spotify_client.py`, you'll construct a `spotipy.oauth2.SpotifyOAuth` object using your client ID, secret, redirect URI, and a scope string. For this phase you only need enough scope to prove login works:

```
scope = "user-top-read user-read-recently-played"
```

**The detail that breaks most multi-user Flask + spotipy tutorials:** by default, spotipy caches the logged-in user's token to a single local file. That's fine for a personal script running as you, but wrong for a webapp with multiple accounts, because every new login overwrites the same file and effectively logs everyone in as whoever authenticated last. Instead:

- Do **not** rely on spotipy's default file cache in your route logic.
- When `/callback` completes, extract the access token and refresh token from the response yourself and store the refresh token as a column on that user's row in MySQL (built in Phase 2).
- On any later request that needs to call the Spotify API on behalf of a user, load their refresh token from the database, use it to get a fresh access token, and make the call. Do this per-request or per-session, not via a shared file.

## Step 8 — Build three routes

- **`/login`** — Use the OAuth object to build the Spotify authorization URL and redirect the browser to it.
- **`/callback`** — Spotify redirects here with a `code` parameter. Exchange it for an access token and refresh token. Call `GET /me` with the access token to get the user's Spotify ID and display name. Check if a user with that `spotify_id` already exists in your database — if not, create one. Save the refresh token on that row. Set a Flask session value (e.g. `session['user_id'] = <your internal user id>`) so subsequent requests know who's logged in.
- **`/logout`** — Clear the session.

You don't have models yet at this point (that's Phase 2) — it's fine to stub the "look up or create user" step with a placeholder and come back to it once Phase 2 is done, or to do Phase 1 and 2 together if you're moving fast. Either order works; just don't consider Phase 1 finished until the database write actually happens.

## Checkpoint — before moving to Phase 2

- [ ] Clicking a "Log in with Spotify" link redirects you to Spotify's real authorization page
- [ ] Approving access redirects you back to `/callback` without an error
- [ ] You can print/log the Spotify user ID and display name returned from `GET /me`
- [ ] Your `.env` file is populated and is **not** tracked by git (`git status` should not list it)
- [ ] You understand why the default spotipy file cache won't work here, even if you haven't built the DB-backed version yet

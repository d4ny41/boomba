# Spotify Rating App — Build Guide Overview

This is a five-phase, follow-along guide for building your Letterboxd-for-songs webapp over a weekend. Work through the files in order — each phase assumes the previous one is finished and tested, not just written.

## Files in this guide

1. `01-environment-and-spotify-setup.md` — Spotify Developer Dashboard, project skeleton, working OAuth login loop
2. `02-database-and-models.md` — MySQL schema, SQLAlchemy models, verifying the data layer
3. `03-core-features-rating-and-feed.md` — recently-played and top-tracks ingestion, the rating page, the personal feed
4. `04-friends-and-stretch-features.md` — friend requests, viewing a friend's list, aggregated feed (stretch)
5. `05-publishing-and-cv-presentation.md` — README, demo capture, deployment, git hygiene, CV framing

Each file ends with a **Checkpoint** section. Do not start the next file until every item in the checkpoint is true. This project fails in the middle if you stack unverified layers — the OAuth loop in particular has to be solid before anything else is worth building.

## What you're building (recap of scope)

**Weekend MVP:** Spotify OAuth login, a page to view and rate your own tracks (from recently-played and top-tracks), a personal feed showing your top tracks with ratings inline.

**Stretch, only if MVP finishes early:** friend requests, viewing a friend's rated list, a basic combined "friend group top tracks" view.

**Explicitly not this weekend:** comments/reviews, genre tagging, any kind of global/public chart (Spotify's Development Mode restrictions rule this out — see the note below), recommendation logic.

## Tech stack (fixed for this build)

- **Backend:** Flask
- **Spotify integration:** `spotipy`
- **Database:** MySQL, accessed via `Flask-SQLAlchemy` + `pymysql`
- **Frontend:** Jinja2 templates + plain CSS
- **Local MySQL:** Docker container, not a native install
- **Auth model:** "Sign in with Spotify" only — no separate password system. A user's identity is their Spotify user ID.

## Environment variables you'll accumulate (reference list)

Keep these in a single `.env` file at the project root, and make sure `.env` is in `.gitignore` before your first commit. You'll fill these in gradually across Phase 1 and Phase 2 — this table is here so you have one place to check you haven't missed one.

| Variable | Set in phase | Purpose |
|---|---|---|
| `SPOTIFY_CLIENT_ID` | 1 | From the Spotify Developer Dashboard |
| `SPOTIFY_CLIENT_SECRET` | 1 | From the Spotify Developer Dashboard |
| `SPOTIFY_REDIRECT_URI` | 1 | Must exactly match what you set in the Dashboard |
| `FLASK_SECRET_KEY` | 1 | Signs the session cookie — any long random string |
| `MYSQL_HOST` | 2 | e.g. `127.0.0.1` |
| `MYSQL_PORT` | 2 | e.g. `3306` |
| `MYSQL_USER` | 2 | From your Docker container config |
| `MYSQL_PASSWORD` | 2 | From your Docker container config |
| `MYSQL_DATABASE` | 2 | e.g. `song_ratings` |

## The constraint that shapes several design decisions

Spotify's Development Mode (which is what this project runs under, since you're not a registered business with 250k+ monthly active users) currently limits you to 5 allowlisted users and restricts several endpoints — no fetching other users' or Spotify's own curated playlists, no batch endpoint fetches, and the app owner needs an active Premium subscription. This is why the "feed" is built from each user's own top tracks rather than a global chart, and why the friends feature searches your own app's user table rather than Spotify's. Every phase below is already designed around this — you don't need to work around it yourself, just be aware of why certain choices were made, since you'll want to explain this on your CV and in interviews (Phase 5 covers that framing).

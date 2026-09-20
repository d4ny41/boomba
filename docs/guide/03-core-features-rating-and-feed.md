# Phase 3 — Rating Page and Personal Feed

**Goal of this phase:** a logged-in user can see a list of tracks they've listened to, assign a 1–5 rating, and see their top tracks with ratings displayed inline on a feed page. This is the core of the product — everything else is secondary to getting this right.

## Step 1 — Fetch recently played tracks

Endpoint: `GET /me/player/recently-played`, scope `user-read-recently-played` (already requested in Phase 1). This is what gives you "the list of music they've listened to" — it's a distinct endpoint from playlists, and it's the app-owner's-own-data kind of call that Spotify's current restrictions still allow.

From each item in the response, extract: the track's Spotify ID, name, artist name(s), album name, album art URL, and `played_at` timestamp.

## Step 2 — Cache track metadata

Before you can rate a track, it needs a row in your `tracks` table. Write a helper function that, given the raw track data from Spotify, does an upsert: check whether a row with that `spotify_track_id` already exists; if not, insert one. Call this helper every time you pull tracks from Spotify (recently-played now, top-tracks below, search later) so you never hit Spotify for metadata you already have.

## Step 3 — Build the rating page

Route: something like `/rate` or `/library`, logged-in only (check the session; redirect to `/login` if absent).

Logic:
1. Pull the current user's recently-played tracks from Spotify.
2. Run each through the caching helper from Step 2 so they all have local `track_id`s.
3. Query the `ratings` table for any existing ratings this user has already given these tracks, so the page can show current scores rather than blank ones.
4. Render a template listing each track with its album art, name, artist, and a 1–5 rating control (five clickable elements or a simple `<select>` — doesn't need to be fancy for v1).
5. On submit, write to `ratings` — because of the unique constraint from Phase 2, this should be an upsert (update `score` and `rated_at` if a row for that `user_id`/`track_id` pair already exists, insert if not).

## Step 4 — Fetch top tracks for the feed

Endpoint: `GET /me/top/tracks`, scope `user-top-read` (already requested). Use the `time_range` query parameter — `short_term` (~4 weeks) is the most natural fit for a "this is what you're into lately" feed, but consider exposing `medium_term` and `long_term` as a toggle later if you have time.

Run the results through the same caching helper as Step 2.

## Step 5 — Build the feed page

Route: `/` or `/feed`, logged-in only.

Logic:
1. Pull the user's top tracks (Step 4).
2. Look up whether each already has a rating from this user.
3. Render each track with its metadata and its rating if one exists, plus a way to rate it directly from the feed (either inline, or a link into the rating page pre-scrolled to that track — inline is more impressive for a demo).

## Step 6 — Manual search (only if time allows)

If a user wants to rate something outside their recently-played or top-tracks lists, you'll want Spotify's search endpoint (`GET /search`, type `track`). Two things to know: the maximum results per request is now 10 rather than the 50 you'll see in older tutorials, and older response fields like `popularity` have been removed — don't build anything that depends on either. A simple search box that shows up to 10 matches is enough; treat this as a nice-to-have, not core.

## Checkpoint — before moving to Phase 4

- [ ] Logging in and visiting the rating page shows your actual recently-played tracks with real metadata
- [ ] Submitting a rating writes to the `ratings` table, and re-rating the same track updates rather than duplicates
- [ ] The feed page shows your real top tracks with any existing ratings displayed correctly
- [ ] You've tested this with at least one other allowlisted account, not just your own, to confirm the per-user data isn't leaking between sessions

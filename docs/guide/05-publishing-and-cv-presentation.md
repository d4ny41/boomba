# Phase 5 — Publishing and CV Presentation

**Goal of this phase:** the project is presentable to someone who has never seen it — a recruiter, an interviewer, a GitHub visitor — within about two minutes of looking at your repo.

## Step 1 — Write the README in this order

1. **One or two sentences** on what the project is and why you built it.
2. **Demo GIF or embedded video near the top** — see Step 2. This is what actually gets looked at; put it before any setup instructions.
3. **Tech stack** — Flask, spotipy, MySQL/SQLAlchemy, plain bullet list.
4. **Setup instructions** — enough that you could hand this to someone else and they could run it locally (env vars needed, Docker command for MySQL, `pip install -r requirements.txt`, how to run the Spotify app registration themselves).
5. **Known limitations** — name the Spotify Development Mode 5-user cap and the restricted-endpoints situation explicitly, in your own words. State plainly that this is a platform constraint, not a bug, and that you designed around it (personal top-tracks feed instead of a global chart; friends drawn from your own user table instead of Spotify's directory). Naming a real external constraint you understood and designed around reads as more competent than a project that quietly pretends it has no limits.
6. **Roadmap** — anything cut for time: comments/reviews, genre tagging, the combined friend feed if you didn't finish it, whatever else you deferred.

## Step 2 — Record the demo instead of relying on a live link

Because of the 5-user cap, a recruiter generally can't just click a link and log in with their own Spotify account. Don't make the live deployment your primary evidence — record a 60–90 second screen capture of the real flow: log in → rate a track → view feed → (if built) view a friend's list. Use your OS's built-in screen recorder; convert to a GIF with a tool like `ffmpeg` or `gifski` if you want it to autoplay inline on GitHub, or just embed/link the video file. This is the single most important artifact in this phase — it works regardless of anyone's Spotify account status.

## Step 3 — Deploy it too, as a secondary artifact

Push the code to a host like Render or Railway (both have usable free tiers for a small Flask app). You'll need a hosted MySQL instance as well — either the provider's managed MySQL add-on if available, or a small external one (PlanetScale, or similar). Set your environment variables in the host's dashboard rather than committing a production `.env`. Treat this as "nice to have a real link in the README" rather than the primary way anyone will experience the project.

## Step 4 — Git hygiene

- Confirm `.env` was never committed at any point in history — check with `git log --all --full-history -- .env`; if it was, that needs cleaning up before the repo goes public, since a leaked secret in history isn't fixed by deleting the file in a later commit.
- Commit progressively rather than in one final dump — ideally your commit history roughly mirrors the phases in this guide (OAuth working, schema in place, rating page working, feed working, friends working). A commit history that shows incremental, testable progress is itself something a reviewer will read.

## Step 5 — Framing it on your CV

A CV line should say what the project demonstrates, not just what it is. Something in the shape of: "Built a full-stack song-rating webapp (Flask, MySQL, Spotify OAuth) as a solo weekend project; designed the data model and auth flow around Spotify's Developer Mode API constraints." That second clause is doing real work — it signals you understood a real-world platform limitation rather than just following a tutorial.

## Step 6 — Being ready to talk about the Spotify constraint in an interview

If asked "why doesn't it show global top songs" or "why is it capped at 5 users," have the short version ready: Spotify's Development Mode restricts apps to a small allowlist and blocks fetching other users' or Spotify-curated playlist data, and going beyond that (Extended Quota) requires being a registered business with a quarter-million monthly active users already — not something reachable from a weekend project. Being able to state that clearly, rather than looking caught out, is exactly the kind of thing this "Known limitations" section is for.

## Checkpoint — done

- [ ] README has the demo GIF/video visible without scrolling past a wall of text first
- [ ] Known limitations section names the 5-user cap explicitly
- [ ] `.env` has never been committed, checked via git history, not just the current `.gitignore`
- [ ] The repo is pushed and (if you chose to) deployed

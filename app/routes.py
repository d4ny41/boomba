import secrets

import spotipy
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from markupsafe import escape
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.auth import login_required
from app.models import Rating, Track, User, db
from app.services import get_or_create_tracks
from app.spotify_client import SpotifyAuthError, get_oauth, get_spotify_for_user

main = Blueprint("main", __name__)


# The only places a POST /rate may send the user back to; never a URL from the form.
NEXT_ENDPOINTS = {"rate": "main.rate", "feed": "main.feed"}
VALID_SCORES = {"1", "2", "3", "4", "5"}


@main.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.feed"))
    return render_template("index.html")


@main.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    return redirect(get_oauth().get_authorize_url(state=state))


@main.route("/callback")
def callback():
    if request.args.get("error"):
        return f"Spotify authorization failed: {escape(request.args['error'])}", 400

    expected_state = session.pop("oauth_state", None)
    if not expected_state or request.args.get("state") != expected_state:
        return "Invalid OAuth state.", 400

    code = request.args.get("code")
    if not code:
        return "Missing authorization code.", 400

    token_info = get_oauth().get_access_token(code, as_dict=True, check_cache=False)
    profile = spotipy.Spotify(auth=token_info["access_token"]).current_user()

    spotify_id = profile["id"]
    display_name = profile.get("display_name") or spotify_id
    current_app.logger.info("Spotify login: id=%s display_name=%s", spotify_id, display_name)

    images = profile.get("images") or []
    image_url = images[0]["url"] if images else None
    refresh_token = token_info.get("refresh_token")

    user = User.query.filter_by(spotify_id=spotify_id).first()
    if user is None:
        if not refresh_token:
            return "Spotify did not return a refresh token.", 502
        user = User(
            spotify_id=spotify_id,
            display_name=display_name,
            profile_image_url=image_url,
            spotify_refresh_token=refresh_token,
        )
        db.session.add(user)
    else:
        user.display_name = display_name
        user.profile_image_url = image_url
        # Spotify only sometimes returns a refresh token; keep the old one otherwise.
        if refresh_token:
            user.spotify_refresh_token = refresh_token
    db.session.commit()

    session["user_id"] = user.id
    session["spotify_id"] = spotify_id
    session["display_name"] = display_name

    return redirect(url_for("main.feed"))


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@main.route("/feed")
@login_required
def feed():
    try:
        sp = get_spotify_for_user(g.user)
    except SpotifyAuthError as e:
        current_app.logger.info("%s", e)
        session.clear()
        flash("Your Spotify session has expired. Please log in again.", "error")
        return redirect(url_for("main.login"))

    # Top-tracks items are track objects directly (no {"track": ...} wrapper),
    # already in rank order.
    items = sp.current_user_top_tracks(limit=20, time_range="short_term")["items"]
    tracks = get_or_create_tracks(items)

    scores = {}
    if tracks:
        ratings = Rating.query.filter(
            Rating.user_id == g.user.id,
            Rating.track_id.in_([t.id for t in tracks]),
        ).all()
        scores = {r.track_id: r.score for r in ratings}

    return render_template("feed.html", tracks=tracks, scores=scores)


@main.route("/rate", methods=["GET"])
@login_required
def rate():
    try:
        sp = get_spotify_for_user(g.user)
    except SpotifyAuthError as e:
        current_app.logger.info("%s", e)
        session.clear()
        flash("Your Spotify session has expired. Please log in again.", "error")
        return redirect(url_for("main.login"))

    items = sp.current_user_recently_played(limit=50)["items"]

    # Items come newest first, so the first time we see a track id is its most recent play.
    seen = set()
    raw_tracks = []
    for item in items:
        track = item.get("track")
        if not track or not track.get("id") or track["id"] in seen:
            continue
        seen.add(track["id"])
        raw_tracks.append(track)

    tracks = get_or_create_tracks(raw_tracks)

    scores = {}
    if tracks:
        ratings = Rating.query.filter(
            Rating.user_id == g.user.id,
            Rating.track_id.in_([t.id for t in tracks]),
        ).all()
        scores = {r.track_id: r.score for r in ratings}

    return render_template("rate.html", tracks=tracks, scores=scores)


@main.route("/rate", methods=["POST"])
@login_required
def rate_submit():
    endpoint = NEXT_ENDPOINTS.get(request.form.get("next"), "main.rate")
    user_id = session["user_id"]

    raw_score = request.form.get("score", "")
    raw_track_id = request.form.get("track_id", "")
    track = None
    if raw_track_id.isascii() and raw_track_id.isdigit() and len(raw_track_id) <= 10:
        track = db.session.get(Track, int(raw_track_id))

    if raw_score not in VALID_SCORES or track is None:
        flash("Invalid rating submission; nothing was saved.", "error")
        return redirect(url_for(endpoint))
    score = int(raw_score)

    # Single-statement upsert on uq_ratings_user_track. rated_at is set explicitly
    # because the model's onupdate doesn't fire for ON DUPLICATE KEY UPDATE.
    stmt = mysql_insert(Rating).values(
        user_id=user_id, track_id=track.id, score=score, rated_at=func.now()
    )
    stmt = stmt.on_duplicate_key_update(score=stmt.inserted.score, rated_at=func.now())
    db.session.execute(stmt)
    db.session.commit()

    flash(f"Rated {track.name}: {score}/5", "success")
    return redirect(url_for(endpoint, _anchor=f"track-{track.id}"))

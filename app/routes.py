import secrets

import spotipy
from flask import (
    Blueprint,
    abort,
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
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.auth import login_required
from app.models import Friendship, Rating, Track, User, db
from app.services import (
    are_friends,
    count_incoming_requests,
    get_friends,
    get_friendship,
    get_or_create_tracks,
    get_relationship,
)
from app.spotify_client import SpotifyAuthError, get_oauth, get_spotify_for_user

main = Blueprint("main", __name__)


# Fixed redirect targets so the form's "next" value can't become an open redirect.
NEXT_ENDPOINTS = {"rate": "main.rate", "feed": "main.feed"}
VALID_SCORES = {"1", "2", "3", "4", "5"}


@main.app_context_processor
def inject_incoming_request_count():
    user_id = session.get("user_id")
    return {"incoming_request_count": count_incoming_requests(user_id) if user_id else 0}


@main.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.feed"))
    return render_template("landing.html")


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

    # Unlike recently played, top-tracks items are bare track objects, already in rank order.
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

    # Recently played repeats tracks; items are newest first, so keep each track's first occurrence.
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

    # rated_at is set explicitly because onupdate doesn't fire for ON DUPLICATE KEY UPDATE.
    stmt = mysql_insert(Rating).values(
        user_id=user_id, track_id=track.id, score=score, rated_at=func.now()
    )
    stmt = stmt.on_duplicate_key_update(score=stmt.inserted.score, rated_at=func.now())
    db.session.execute(stmt)
    db.session.commit()

    flash(f"Rated {track.name}: {score}/5", "success")
    return redirect(url_for(endpoint, _anchor=f"track-{track.id}"))


@main.route("/friends")
@login_required
def friends():
    me = g.user.id

    incoming = (
        Friendship.query.filter_by(friend_id=me, status="pending")
        .order_by(Friendship.created_at.desc())
        .all()
    )
    outgoing = (
        Friendship.query.filter_by(user_id=me, status="pending")
        .order_by(Friendship.created_at.desc())
        .all()
    )

    # Pending and accepted connections are already listed above.
    rows = Friendship.query.filter(
        or_(Friendship.user_id == me, Friendship.friend_id == me)
    ).all()
    connected = {r.friend_id if r.user_id == me else r.user_id for r in rows}
    others = (
        User.query.filter(User.id != me, User.id.notin_(connected))
        .order_by(User.display_name)
        .all()
    )

    return render_template(
        "friends.html",
        incoming=incoming,
        outgoing=outgoing,
        friends=get_friends(me),
        others=others,
    )


@main.route("/friends/request/<int:user_id>", methods=["POST"])
@login_required
def friend_request(user_id):
    me = session["user_id"]
    target = db.session.get(User, user_id)
    if target is None:
        abort(404)
    if target.id == me:
        flash("You can't send a friend request to yourself.", "error")
        return redirect(url_for("main.friends"))

    rel = get_relationship(me, target.id)
    if rel is None:
        db.session.add(Friendship(user_id=me, friend_id=target.id, status="pending"))
        db.session.commit()
        flash(f"Friend request sent to {target.display_name}.", "success")
    elif rel.status == "accepted":
        flash(f"You're already friends with {target.display_name}.", "error")
    elif rel.user_id == me:
        flash(f"You've already sent {target.display_name} a request.", "error")
    else:
        # They already asked us, so treat this as accepting their request.
        rel.status = "accepted"
        db.session.commit()
        flash(f"You're now friends with {target.display_name}.", "success")
    return redirect(url_for("main.friends"))


def _incoming_request_or_404(request_id):
    row = db.session.get(Friendship, request_id)
    if row is None or row.status != "pending" or row.friend_id != session["user_id"]:
        abort(404)
    return row


@main.route("/friends/accept/<int:request_id>", methods=["POST"])
@login_required
def friend_accept(request_id):
    row = _incoming_request_or_404(request_id)
    row.status = "accepted"
    db.session.commit()
    flash(f"You're now friends with {row.sender.display_name}.", "success")
    return redirect(url_for("main.friends"))


@main.route("/friends/decline/<int:request_id>", methods=["POST"])
@login_required
def friend_decline(request_id):
    row = _incoming_request_or_404(request_id)
    name = row.sender.display_name
    db.session.delete(row)
    db.session.commit()
    flash(f"Declined the request from {name}.", "success")
    return redirect(url_for("main.friends"))


@main.route("/friends/cancel/<int:request_id>", methods=["POST"])
@login_required
def friend_cancel(request_id):
    row = db.session.get(Friendship, request_id)
    if row is None or row.status != "pending" or row.user_id != session["user_id"]:
        abort(404)
    name = row.recipient.display_name
    db.session.delete(row)
    db.session.commit()
    flash(f"Cancelled your request to {name}.", "success")
    return redirect(url_for("main.friends"))


@main.route("/friends/remove/<int:user_id>", methods=["POST"])
@login_required
def friend_remove(user_id):
    row = get_friendship(session["user_id"], user_id)
    if row is None:
        abort(404)
    other = row.recipient if row.user_id == session["user_id"] else row.sender
    name = other.display_name
    db.session.delete(row)
    db.session.commit()
    flash(f"Removed {name} from your friends.", "success")
    return redirect(url_for("main.friends"))


@main.route("/friends/<int:user_id>/ratings")
@login_required
def friend_ratings(user_id):
    if user_id == g.user.id:
        return redirect(url_for("main.rate"))
    # 404 rather than 403 so this doesn't reveal whether the user exists.
    if not are_friends(g.user.id, user_id):
        abort(404)
    friend = db.session.get(User, user_id)

    # No Spotify calls here; this page reads only our database.
    rows = (
        db.session.query(Rating, Track)
        .join(Track, Rating.track_id == Track.id)
        .filter(Rating.user_id == friend.id)
        .order_by(Rating.score.desc(), Rating.rated_at.desc())
        .all()
    )

    my_scores = {}
    if rows:
        mine = Rating.query.filter(
            Rating.user_id == g.user.id,
            Rating.track_id.in_([t.id for _, t in rows]),
        ).all()
        my_scores = {r.track_id: r.score for r in mine}

    return render_template(
        "friend_ratings.html", friend=friend, rows=rows, my_scores=my_scores
    )

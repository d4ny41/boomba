import secrets

import spotipy
from flask import (
    Blueprint,
    current_app,
    redirect,
    request,
    session,
    url_for,
)
from markupsafe import escape

from app.models import User, db
from app.spotify_client import get_oauth

main = Blueprint("main", __name__)


@main.route("/")
def index():
    name = session.get("display_name")
    if name:
        return (
            f"<p>Logged in as {escape(name)} ({escape(session['spotify_id'])})</p>"
            f'<p><a href="{url_for("main.logout")}">Log out</a></p>'
        )
    return f'<p><a href="{url_for("main.login")}">Log in with Spotify</a></p>'


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

    return redirect(url_for("main.index"))


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))

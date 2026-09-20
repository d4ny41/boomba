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

    # TODO (Phase 2): look up or create the User row by spotify_id, save
    # token_info["refresh_token"] on it, and set session["user_id"] to the
    # internal user id. Until models exist, keep the Spotify identity in the
    # session only so the home page can show who is logged in.
    session["spotify_id"] = spotify_id
    session["display_name"] = display_name

    return redirect(url_for("main.index"))


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))

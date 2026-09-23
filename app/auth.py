from functools import wraps

from flask import g, redirect, session, url_for

from app.models import User, db


def login_required(view):
    """Redirect to /login unless logged in; exposes the current User as g.user."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return redirect(url_for("main.login"))

        user = db.session.get(User, user_id)
        if user is None:
            # Stale session pointing at a user row that no longer exists.
            session.clear()
            return redirect(url_for("main.login"))

        g.user = user
        return view(*args, **kwargs)

    return wrapped

import logging
from urllib.parse import urlparse

from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from app.config import Config
from app.models import db

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    app.logger.setLevel(logging.INFO)

    db.init_app(app)
    # Signs tokens with SECRET_KEY, which Config loads from FLASK_SECRET_KEY.
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Your session expired, please try again", "error")
        # Only bounce back to our own pages; a cross-site referrer would
        # otherwise turn this into an open redirect.
        referrer = request.referrer
        if referrer and urlparse(referrer).netloc == request.host:
            return redirect(referrer)
        return redirect(url_for("main.feed"))

    from app.routes import main

    app.register_blueprint(main)
    return app

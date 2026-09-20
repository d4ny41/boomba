import logging

from flask import Flask

from app.config import Config


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    app.logger.setLevel(logging.INFO)

    from app.routes import main

    app.register_blueprint(main)
    return app

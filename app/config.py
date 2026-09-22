import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

_REQUIRED = (
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REDIRECT_URI",
    "FLASK_SECRET_KEY",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
)

_missing = [name for name in _REQUIRED if not os.getenv(name)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")


class Config:
    SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
    SPOTIFY_REDIRECT_URI = os.environ["SPOTIFY_REDIRECT_URI"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(os.environ['MYSQL_USER'])}"
        f":{quote_plus(os.environ['MYSQL_PASSWORD'])}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}"
        f"/{os.environ['MYSQL_DATABASE']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

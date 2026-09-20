import os

from dotenv import load_dotenv

load_dotenv()

_REQUIRED = (
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REDIRECT_URI",
    "FLASK_SECRET_KEY",
)

_missing = [name for name in _REQUIRED if not os.getenv(name)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")


class Config:
    SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
    SPOTIFY_REDIRECT_URI = os.environ["SPOTIFY_REDIRECT_URI"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

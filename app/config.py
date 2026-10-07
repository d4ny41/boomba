import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# init_db.py can point BOOMBA_ENV_FILE at another file; real env vars still take precedence.
load_dotenv(os.getenv("BOOMBA_ENV_FILE"))

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

APP_ENV = os.getenv("APP_ENV", "development")
# Reject typos like "prod" rather than silently running with dev settings.
if APP_ENV not in ("development", "production"):
    raise RuntimeError(f"APP_ENV must be 'development' or 'production', got {APP_ENV!r}")
IS_PRODUCTION = APP_ENV == "production"

# Hosted MySQL (Aiven) requires TLS; local Docker MySQL connects without it.
MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA")
if MYSQL_SSL_CA and not os.path.isfile(MYSQL_SSL_CA):
    raise RuntimeError(f"MYSQL_SSL_CA points to a missing file: {MYSQL_SSL_CA}")

GITHUB_REPO_URL = "https://github.com/d4ny41/boomba"
DEMO_VIDEO_URL = "https://github.com/d4ny41/boomba#demo"


class Config:
    SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
    SPOTIFY_REDIRECT_URI = os.environ["SPOTIFY_REDIRECT_URI"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    # Defence in depth alongside CSRFProtect.
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    if IS_PRODUCTION:
        # Local dev runs over plain HTTP, where a Secure cookie would never be sent.
        SESSION_COOKIE_SECURE = True
        DEBUG = False

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(os.environ['MYSQL_USER'])}"
        f":{quote_plus(os.environ['MYSQL_PASSWORD'])}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}"
        f"/{os.environ['MYSQL_DATABASE']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Hosted MySQL drops idle connections, so ping before use and recycle before its timeout.
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    if MYSQL_SSL_CA:
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"ssl": {"ca": MYSQL_SSL_CA}}

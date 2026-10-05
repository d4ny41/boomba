"""One-off script: create all tables defined in app/models.py.

    python init_db.py                            # uses .env (local Docker MySQL)
    python init_db.py --env-file .env.production # uses the hosted database
"""

import argparse
import os
import sys

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--env-file", default=".env", help="dotenv file to load (default: .env)")
args = parser.parse_args()

if args.env_file != ".env":
    if not os.path.isfile(args.env_file):
        sys.exit(f"Env file not found: {args.env_file}")
    # Must be set before importing app, since app.config loads the env file on import.
    os.environ["BOOMBA_ENV_FILE"] = args.env_file

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402

app = create_app()

with app.app_context():
    print("Database:", db.engine.url.render_as_string(hide_password=True))
    db.create_all()
    print("Tables created:", ", ".join(sorted(db.metadata.tables)))

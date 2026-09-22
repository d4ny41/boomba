"""One-off script: create all tables defined in app/models.py."""

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created:", ", ".join(sorted(db.metadata.tables)))

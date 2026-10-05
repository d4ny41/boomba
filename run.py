import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug is opt-in via FLASK_DEBUG; never default it on, the debugger allows code execution.
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    # Use 127.0.0.1 (not localhost) to match the registered Spotify redirect URI.
    app.run(host="127.0.0.1", port=5000, debug=debug)

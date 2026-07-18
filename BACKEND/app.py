"""
BACKEND/app.py
--------------
Flask application entry point.

Run this file to start the development server:
    cd BACKEND
    python app.py

Or from the project root with the venv active:
    venv\\Scripts\\python BACKEND\\app.py
"""

import os
import sys
import logging

# ---------------------------------------------------------------------------
# Ensure BACKEND/ is on sys.path so all relative imports work correctly
# regardless of the current working directory.
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from flask import Flask, redirect, url_for, render_template

import config
from database.db import init_db

# ---------------------------------------------------------------------------
# Logging — configure before anything else to capture startup messages.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve FRONTEND paths relative to this file so the app works from any cwd.
# ---------------------------------------------------------------------------
_PROJECT_ROOT   = os.path.dirname(_BACKEND_DIR)
_TEMPLATE_FOLDER = os.path.join(_PROJECT_ROOT, "FRONTEND", "templates")
_STATIC_FOLDER   = os.path.join(_PROJECT_ROOT, "FRONTEND", "static")

# ---------------------------------------------------------------------------
# Create the Flask application instance.
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder=_TEMPLATE_FOLDER,
    static_folder=_STATIC_FOLDER,
)

# Load all settings from config.py into Flask's config dict.
app.secret_key                  = config.SECRET_KEY
app.config["DEBUG"]             = config.DEBUG
app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME
app.config["SESSION_COOKIE_HTTPONLY"]    = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"]    = config.SESSION_COOKIE_SAMESITE
app.config["SESSION_COOKIE_SECURE"]      = config.SESSION_COOKIE_SECURE

# ---------------------------------------------------------------------------
# Initialise the database (creates tables + seeds test data on first run).
# ---------------------------------------------------------------------------
with app.app_context():
    init_db()
    logger.info("Database ready.")

# ---------------------------------------------------------------------------
# Register Blueprints — the order does not matter for correctness.
# ---------------------------------------------------------------------------
from routes.auth         import auth_bp
from routes.dashboard    import dashboard_bp
from routes.transactions import transactions_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(transactions_bp)

logger.info("Blueprints registered: auth, dashboard, transactions")

# ---------------------------------------------------------------------------
# Root route — redirect visitors straight to /login.
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("auth.login"))

# ---------------------------------------------------------------------------
# Custom error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled 500 error: %s", e)
    return render_template("errors/500.html"), 500

# ---------------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Banking Workshop app on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=config.DEBUG)

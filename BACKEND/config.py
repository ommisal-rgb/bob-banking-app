"""
BACKEND/config.py
-----------------
Central configuration for the Banking application.
All environment-specific settings live here. Nothing else should hard-code
sensitive values or paths.
"""

import os
from datetime import timedelta

# ---------------------------------------------------------------------------
# Base directory — resolves to the BACKEND/ folder regardless of where
# the process is launched from.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Secret key — signs Flask session cookies.
# Override via the SECRET_KEY environment variable in production.
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "banking-workshop-dev-secret-key-change-in-production-2024!"
)

# ---------------------------------------------------------------------------
# SQLite database file path
# ---------------------------------------------------------------------------
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "database", "banking.db")
)

# ---------------------------------------------------------------------------
# Flask debug flag — must be False in any non-development environment.
# ---------------------------------------------------------------------------
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Session lifetime — how long a "remember me" session stays alive.
# ---------------------------------------------------------------------------
PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

# ---------------------------------------------------------------------------
# Session cookie security settings
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
# Set to True only when HTTPS is available (production)
SESSION_COOKIE_SECURE = False

"""
BACKEND/routes/auth.py
-----------------------
Blueprint: auth
URL prefix: /

Handles login and logout.  Routes are thin wrappers: read the HTTP request,
call the appropriate service function, return an HTTP response.
"""

import logging
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from services.auth_service import verify_login

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Login-required decorator (defined here; imported by other route modules)
# ---------------------------------------------------------------------------

def login_required(f):
    """
    Decorator that redirects unauthenticated users to /login.
    Apply to every route that requires a logged-in session.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If the user is already authenticated, skip the login form.
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    # POST — process the submitted form.
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    result = verify_login(username, password)

    if result["success"]:
        session.clear()                          # Prevent session fixation
        session["user_id"]   = result["user_id"]
        session["full_name"] = result["full_name"]
        session.permanent    = True              # Enables PERMANENT_SESSION_LIFETIME
        logger.info("User %s logged in (id=%s)", username, result["user_id"])
        return redirect(url_for("dashboard.dashboard"))

    # Failed login — re-render with error message.
    flash(result["error"], "danger")
    return render_template("login.html", username=username), 401


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    logger.info("User id=%s logged out.", user_id)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

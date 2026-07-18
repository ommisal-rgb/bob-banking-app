"""
BACKEND/services/auth_service.py
---------------------------------
Business logic for authentication.

Routes call these functions; this module never imports Flask's request object
or renders templates — it is HTTP-agnostic and therefore independently testable.
"""

import logging
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_one

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_login(username: str, password: str) -> dict:
    """
    Verify a login attempt.

    Returns a dict with:
        success (bool)
        user_id (int | None)
        full_name (str | None)
        error (str | None)

    Security note: the same generic error message is returned whether the
    username does not exist OR the password is wrong. This prevents an
    attacker from enumerating valid usernames.
    """
    # Validate that both fields are non-empty before touching the database.
    if not username or not username.strip():
        return {"success": False, "user_id": None, "full_name": None,
                "error": "Please enter a username."}

    if not password:
        return {"success": False, "user_id": None, "full_name": None,
                "error": "Please enter a password."}

    # Look up the customer record.
    customer = get_one(
        "SELECT id, password_hash, full_name FROM customers WHERE username = ?",
        (username.strip(),)
    )

    # Use a constant-time comparison to avoid timing attacks.
    # If no customer was found we still call check_password_hash with a dummy
    # hash so the function always takes roughly the same time.
    _DUMMY_HASH = generate_password_hash("dummy-compare-placeholder")
    stored_hash = customer["password_hash"] if customer else _DUMMY_HASH

    password_ok = check_password_hash(stored_hash, password)

    if customer is None or not password_ok:
        logger.warning("Failed login attempt for username: %s", username)
        return {"success": False, "user_id": None, "full_name": None,
                "error": "Invalid username or password."}

    logger.info("Successful login for user_id=%s", customer["id"])
    return {
        "success": True,
        "user_id": customer["id"],
        "full_name": customer["full_name"],
        "error": None,
    }


def hash_password(plain_text_password: str) -> str:
    """
    Hash a plain-text password using Werkzeug's secure hashing algorithm.
    Used during database seeding and any future registration flow.
    Never store the plain-text password.
    """
    return generate_password_hash(plain_text_password)

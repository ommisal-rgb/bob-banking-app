"""
TESTS/test_auth_service.py
---------------------------
Unit tests for BACKEND/services/auth_service.py.
The database is mocked so no real SQLite file is needed.
"""

import sys
import os
import unittest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make BACKEND importable from TESTS/
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "BACKEND")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Patch config DATABASE_PATH before importing the service so no real DB file
# is touched during unit tests.
os.environ.setdefault("DATABASE_PATH", ":memory:")

from werkzeug.security import generate_password_hash
from services.auth_service import verify_login, hash_password


class TestHashPassword(unittest.TestCase):

    def test_returns_non_plain_text(self):
        plain = "mysecretpassword"
        hashed = hash_password(plain)
        self.assertNotEqual(plain, hashed)

    def test_hash_verifiable(self):
        from werkzeug.security import check_password_hash
        plain = "testpass"
        hashed = hash_password(plain)
        self.assertTrue(check_password_hash(hashed, plain))

    def test_different_hashes_same_input(self):
        """Werkzeug includes a salt, so two hashes of the same password differ."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        self.assertNotEqual(h1, h2)


class TestVerifyLogin(unittest.TestCase):

    def _make_customer(self, username="alice", password="pass123", full_name="Alice"):
        return {
            "id": 1,
            "username": username,
            "password_hash": generate_password_hash(password),
            "full_name": full_name,
        }

    @patch("services.auth_service.get_one")
    def test_correct_credentials(self, mock_get_one):
        customer = self._make_customer()
        mock_get_one.return_value = customer
        result = verify_login("alice", "pass123")
        self.assertTrue(result["success"])
        self.assertEqual(result["user_id"], 1)
        self.assertEqual(result["full_name"], "Alice")
        self.assertIsNone(result["error"])

    @patch("services.auth_service.get_one")
    def test_wrong_password(self, mock_get_one):
        customer = self._make_customer()
        mock_get_one.return_value = customer
        result = verify_login("alice", "wrongpassword")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid username or password.")

    @patch("services.auth_service.get_one")
    def test_unknown_username(self, mock_get_one):
        mock_get_one.return_value = None
        result = verify_login("nobody", "somepass")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid username or password.")

    def test_empty_username(self):
        result = verify_login("", "somepass")
        self.assertFalse(result["success"])
        self.assertIn("username", result["error"].lower())

    def test_empty_password(self):
        result = verify_login("alice", "")
        self.assertFalse(result["success"])
        self.assertIn("password", result["error"].lower())

    def test_whitespace_only_username(self):
        result = verify_login("   ", "somepass")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()

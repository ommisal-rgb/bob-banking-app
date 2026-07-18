"""
TESTS/test_integration.py
--------------------------
Integration tests using Flask's test client backed by a real (temporary) SQLite
database file that is created fresh for every test case.
"""

import sys
import os
import sqlite3
import unittest
import tempfile

# ---------------------------------------------------------------------------
# Bootstrap path before any BACKEND imports
# ---------------------------------------------------------------------------
_BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BACKEND")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _build_fresh_db(path: str) -> None:
    """Create schema + one test user in the SQLite file at *path*."""
    from werkzeug.security import generate_password_hash
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            full_name     TEXT    NOT NULL,
            balance       REAL    NOT NULL DEFAULT 0.0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            type        TEXT    NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
            amount      REAL    NOT NULL,
            timestamp   TEXT    NOT NULL
        );
    """)
    conn.execute(
        "INSERT INTO customers (username, password_hash, full_name, balance) VALUES (?,?,?,?)",
        ("testuser", generate_password_hash("testpassword"), "Test User", 500.00),
    )
    conn.commit()
    conn.close()


class BankingIntegrationTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # setUp / tearDown
    # ------------------------------------------------------------------

    def setUp(self):
        # Create a temporary DB file for this test.
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        _build_fresh_db(self._tmp.name)

        # Patch the DATABASE_PATH in all modules that have already cached it.
        import config as cfg_module
        import database.db as db_module
        cfg_module.DATABASE_PATH = self._tmp.name
        db_module.DATABASE_PATH = self._tmp.name

        # Import app AFTER patching paths.
        # Use importlib so we get a fresh reference without re-executing module code.
        import importlib
        import app as app_module
        importlib.reload(app_module)          # re-wires blueprints against fresh config
        self._app = app_module.app
        self._app.config["TESTING"] = True
        self._app.secret_key = "integration-test-secret"

        self.client = self._app.test_client()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _login(self, username="testuser", password="testpassword", follow=False):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=follow,
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_get_login_returns_200(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sign In", resp.data)

    def test_login_correct_credentials_redirects_to_dashboard(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers.get("Location", ""))

    def test_login_wrong_password_shows_error(self):
        resp = self._login("testuser", "wrongpassword", follow=True)
        self.assertIn(b"Invalid username or password", resp.data)

    def test_login_unknown_user_shows_error(self):
        resp = self._login("ghost", "pass", follow=True)
        self.assertIn(b"Invalid username or password", resp.data)

    # ------------------------------------------------------------------
    # Session guard
    # ------------------------------------------------------------------

    def test_dashboard_unauthenticated_redirects(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_deposit_unauthenticated_redirects(self):
        resp = self.client.get("/deposit")
        self.assertEqual(resp.status_code, 302)

    def test_withdraw_unauthenticated_redirects(self):
        resp = self.client.get("/withdraw")
        self.assertEqual(resp.status_code, 302)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def test_dashboard_shows_name_and_balance(self):
        self._login()
        resp = self.client.get("/dashboard", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Test User", resp.data)
        self.assertIn(b"500.00", resp.data)

    # ------------------------------------------------------------------
    # Deposit
    # ------------------------------------------------------------------

    def test_deposit_valid_increases_balance(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "100"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"600.00", resp.data)

    def test_deposit_zero_shows_error(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", resp.data)

    def test_deposit_negative_shows_error(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "-50"}, follow_redirects=True)
        self.assertNotIn(b"600", resp.data)

    def test_deposit_non_numeric_shows_error(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        self.assertIn(b"valid", resp.data.lower())

    # ------------------------------------------------------------------
    # Withdrawal
    # ------------------------------------------------------------------

    def test_withdraw_valid_decreases_balance(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "200"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"300.00", resp.data)

    def test_withdraw_exact_balance_reaches_zero(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "500"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"0.00", resp.data)

    def test_withdraw_insufficient_funds_error(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "1000"}, follow_redirects=True)
        self.assertIn(b"Insufficient", resp.data)

    def test_withdraw_zero_shows_error(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", resp.data)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def test_logout_redirects_to_login(self):
        self._login()
        resp = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_dashboard_after_logout_redirects_to_login(self):
        self._login()
        self.client.get("/logout")
        resp = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()

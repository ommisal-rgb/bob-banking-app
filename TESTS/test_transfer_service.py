"""
TESTS/test_transfer_service.py
--------------------------------
Unit tests for BACKEND/services/transfer_service.py.
Database calls are mocked so no real SQLite file is needed.
"""

import sys, os, unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

_BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BACKEND")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_PATH", ":memory:")

from services.transfer_service import transfer


def _make_sender(balance=500.0, pin="1234"):
    return {
        "id": 1, "username": "admin", "full_name": "Admin User",
        "balance": balance,
        "pin_hash": generate_password_hash(pin),
    }

def _make_recipient(balance=100.0):
    return {
        "id": 2, "username": "alice", "full_name": "Alice Smith",
        "balance": balance,
    }


class TestTransfer(unittest.TestCase):

    @patch("services.transfer_service.execute_transaction")
    @patch("services.transfer_service.get_one")
    def test_valid_transfer(self, mock_get, mock_exec):
        mock_get.side_effect = [_make_sender(), _make_recipient()]
        result = transfer(1, "alice", "100", "1234")
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["balance"], 400.0)
        self.assertEqual(result["recipient_name"], "Alice Smith")
        mock_exec.assert_called_once()

    @patch("services.transfer_service.get_one")
    def test_wrong_pin(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "100", "0000")
        self.assertFalse(result["success"])
        self.assertIn("PIN", result["error"])

    @patch("services.transfer_service.get_one")
    def test_unknown_recipient(self, mock_get):
        mock_get.side_effect = [_make_sender(), None]
        result = transfer(1, "ghost", "50", "1234")
        self.assertFalse(result["success"])
        self.assertIn("No account found", result["error"])

    @patch("services.transfer_service.get_one")
    def test_insufficient_funds(self, mock_get):
        mock_get.side_effect = [_make_sender(balance=20.0), _make_recipient()]
        result = transfer(1, "alice", "50", "1234")
        self.assertFalse(result["success"])
        self.assertIn("Insufficient", result["error"])

    @patch("services.transfer_service.get_one")
    def test_zero_amount(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "0", "1234")
        self.assertFalse(result["success"])
        self.assertIn("greater than zero", result["error"])

    @patch("services.transfer_service.get_one")
    def test_negative_amount(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "-50", "1234")
        self.assertFalse(result["success"])

    @patch("services.transfer_service.get_one")
    def test_non_numeric_amount(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "abc", "1234")
        self.assertFalse(result["success"])
        self.assertIn("valid", result["error"].lower())

    @patch("services.transfer_service.get_one")
    def test_exceeds_max(self, mock_get):
        mock_get.return_value = _make_sender(balance=999999.0)
        result = transfer(1, "alice", "20000", "1234")
        self.assertFalse(result["success"])
        self.assertIn("cannot exceed", result["error"])

    @patch("services.transfer_service.get_one")
    def test_transfer_to_self(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "admin", "50", "1234")
        self.assertFalse(result["success"])
        self.assertIn("yourself", result["error"])

    @patch("services.transfer_service.get_one")
    def test_empty_recipient(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "", "50", "1234")
        self.assertFalse(result["success"])

    @patch("services.transfer_service.get_one")
    def test_empty_pin(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "50", "")
        self.assertFalse(result["success"])
        self.assertIn("PIN", result["error"])

    @patch("services.transfer_service.get_one")
    def test_empty_amount(self, mock_get):
        mock_get.return_value = _make_sender()
        result = transfer(1, "alice", "", "1234")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()

"""
TESTS/test_account_service.py
-------------------------------
Unit tests for BACKEND/services/account_service.py.
The database layer is mocked so no real SQLite file is needed.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

_BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BACKEND")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_PATH", ":memory:")

from services.account_service import deposit, withdraw, get_balance


class TestDeposit(unittest.TestCase):

    @patch("services.account_service.execute_transaction")
    @patch("services.account_service.get_balance", return_value=100.0)
    def test_valid_deposit(self, mock_balance, mock_exec):
        result = deposit(1, "50.00")
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["balance"], 150.0)
        mock_exec.assert_called_once()

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_zero_amount(self, _):
        result = deposit(1, "0")
        self.assertFalse(result["success"])
        self.assertIn("greater than zero", result["error"])

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_negative_amount(self, _):
        result = deposit(1, "-10")
        self.assertFalse(result["success"])

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_non_numeric_amount(self, _):
        result = deposit(1, "abc")
        self.assertFalse(result["success"])
        self.assertIn("valid", result["error"].lower())

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_empty_amount(self, _):
        result = deposit(1, "")
        self.assertFalse(result["success"])

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_exceeds_max(self, _):
        result = deposit(1, "2000000")
        self.assertFalse(result["success"])
        self.assertIn("maximum", result["error"].lower())


class TestWithdraw(unittest.TestCase):

    @patch("services.account_service.execute_transaction")
    @patch("services.account_service.get_balance", return_value=200.0)
    def test_valid_withdrawal(self, mock_balance, mock_exec):
        result = withdraw(1, "75.00")
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["balance"], 125.0)
        mock_exec.assert_called_once()

    @patch("services.account_service.get_balance", return_value=50.0)
    def test_insufficient_funds(self, _):
        result = withdraw(1, "100.00")
        self.assertFalse(result["success"])
        self.assertIn("Insufficient", result["error"])

    @patch("services.account_service.execute_transaction")
    @patch("services.account_service.get_balance", return_value=100.0)
    def test_exact_balance(self, mock_balance, mock_exec):
        result = withdraw(1, "100.00")
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["balance"], 0.0)

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_zero_amount(self, _):
        result = withdraw(1, "0")
        self.assertFalse(result["success"])

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_negative_amount(self, _):
        result = withdraw(1, "-5")
        self.assertFalse(result["success"])

    @patch("services.account_service.get_balance", return_value=100.0)
    def test_non_numeric(self, _):
        result = withdraw(1, "xyz")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()

"""
BACKEND/services/account_service.py
-------------------------------------
Business logic for balance enquiries, deposits, and withdrawals.

All database writes that change both the balance AND log a transaction are
wrapped in a single atomic database transaction to prevent partial updates.
"""

import logging
from datetime import datetime, timezone
from database.db import get_one, execute_transaction

logger = logging.getLogger(__name__)

# Maximum single-transaction amount (configurable guard rail).
MAX_TRANSACTION_AMOUNT = 1_000_000.00


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_amount(raw) -> tuple[float | None, str | None]:
    """
    Convert *raw* (from a form field) to a float.
    Returns (amount, None) on success or (None, error_message) on failure.
    """
    if raw is None or str(raw).strip() == "":
        return None, "Amount is required."
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None, "Please enter a valid numeric amount."
    return value, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_account(customer_id: int) -> dict | None:
    """
    Return the customer row (id, username, full_name, balance) or None.
    """
    return get_one(
        "SELECT id, username, full_name, balance FROM customers WHERE id = ?",
        (customer_id,)
    )


def get_balance(customer_id: int) -> float:
    """Return the current balance for *customer_id*."""
    row = get_one("SELECT balance FROM customers WHERE id = ?", (customer_id,))
    if row is None:
        raise ValueError(f"Customer {customer_id} not found.")
    return row["balance"]


def get_transactions(customer_id: int) -> list[dict]:
    """Return all transactions for *customer_id*, most recent first."""
    from database.db import get_many
    return get_many(
        "SELECT type, amount, timestamp, related_user FROM transactions "
        "WHERE customer_id = ? ORDER BY id DESC",
        (customer_id,)
    )


def deposit(customer_id: int, raw_amount) -> dict:
    """
    Deposit *raw_amount* into *customer_id*'s account.

    Returns:
        {"success": True,  "balance": new_balance}
        {"success": False, "error": error_message}
    """
    amount, err = _parse_amount(raw_amount)
    if err:
        return {"success": False, "error": err}

    if amount <= 0:
        return {"success": False, "error": "Deposit amount must be greater than zero."}

    if amount > MAX_TRANSACTION_AMOUNT:
        return {"success": False, "error": f"Amount exceeds the maximum limit of £{MAX_TRANSACTION_AMOUNT:,.2f}."}

    current_balance = get_balance(customer_id)
    new_balance = current_balance + amount

    execute_transaction([
        (
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id)
        ),
        (
            "INSERT INTO transactions (customer_id, type, amount, timestamp) VALUES (?,?,?,?)",
            (customer_id, "deposit", amount, _now_iso())
        ),
    ])

    logger.info("Deposit: customer_id=%s  amount=%.2f  new_balance=%.2f", customer_id, amount, new_balance)
    return {"success": True, "balance": new_balance}


def withdraw(customer_id: int, raw_amount) -> dict:
    """
    Withdraw *raw_amount* from *customer_id*'s account.

    Returns:
        {"success": True,  "balance": new_balance}
        {"success": False, "error": error_message}
    """
    amount, err = _parse_amount(raw_amount)
    if err:
        return {"success": False, "error": err}

    if amount <= 0:
        return {"success": False, "error": "Withdrawal amount must be greater than zero."}

    if amount > MAX_TRANSACTION_AMOUNT:
        return {"success": False, "error": f"Amount exceeds the maximum limit of £{MAX_TRANSACTION_AMOUNT:,.2f}."}

    current_balance = get_balance(customer_id)

    if current_balance < amount:
        return {"success": False, "error": "Insufficient funds. Your current balance is £{:.2f}.".format(current_balance)}

    new_balance = current_balance - amount

    execute_transaction([
        (
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id)
        ),
        (
            "INSERT INTO transactions (customer_id, type, amount, timestamp) VALUES (?,?,?,?)",
            (customer_id, "withdrawal", amount, _now_iso())
        ),
    ])

    logger.info("Withdrawal: customer_id=%s  amount=%.2f  new_balance=%.2f", customer_id, amount, new_balance)
    return {"success": True, "balance": new_balance}

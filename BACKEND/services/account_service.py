"""
BACKEND/services/account_service.py  (feature/withdraw-validation)
-------------------------------------------------------------------
Withdrawal validation — three explicit checks added to withdraw():
  1. amount must be a positive number
  2. amount must not exceed the MAX_TRANSACTION_AMOUNT ceiling
  3. balance must be sufficient (balance >= amount)
"""

import logging
from datetime import datetime, timezone
from database.db import get_one, execute_transaction

logger = logging.getLogger(__name__)

MAX_TRANSACTION_AMOUNT = 1_000_000.00


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_amount(raw):
    if raw is None or str(raw).strip() == "":
        return None, "Amount is required."
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None, "Please enter a valid numeric amount."
    return value, None


def get_account(customer_id):
    return get_one(
        "SELECT id, username, full_name, balance FROM customers WHERE id = ?",
        (customer_id,)
    )


def get_balance(customer_id):
    row = get_one("SELECT balance FROM customers WHERE id = ?", (customer_id,))
    if row is None:
        raise ValueError(f"Customer {customer_id} not found.")
    return row["balance"]


def get_transactions(customer_id):
    from database.db import get_many
    return get_many(
        "SELECT type, amount, timestamp FROM transactions "
        "WHERE customer_id = ? ORDER BY id DESC",
        (customer_id,)
    )


def deposit(customer_id, raw_amount):
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
        ("UPDATE customers SET balance = ? WHERE id = ?", (new_balance, customer_id)),
        ("INSERT INTO transactions (customer_id, type, amount, timestamp) VALUES (?,?,?,?)",
         (customer_id, "deposit", amount, _now_iso())),
    ])
    return {"success": True, "balance": new_balance}


def withdraw(customer_id, raw_amount):
    # Validation check 1: parse and require a valid positive number
    amount, err = _parse_amount(raw_amount)
    if err:
        return {"success": False, "error": err}

    if amount <= 0:
        return {"success": False, "error": "Withdrawal amount must be greater than zero."}

    # Validation check 2: enforce maximum transaction ceiling
    if amount > MAX_TRANSACTION_AMOUNT:
        return {"success": False, "error": f"Amount exceeds the maximum limit of £{MAX_TRANSACTION_AMOUNT:,.2f}."}

    # Validation check 3: ensure sufficient funds
    current_balance = get_balance(customer_id)
    if current_balance < amount:
        return {"success": False, "error": "Insufficient funds. Your current balance is £{:.2f}.".format(current_balance)}

    new_balance = current_balance - amount
    execute_transaction([
        ("UPDATE customers SET balance = ? WHERE id = ?", (new_balance, customer_id)),
        ("INSERT INTO transactions (customer_id, type, amount, timestamp) VALUES (?,?,?,?)",
         (customer_id, "withdrawal", amount, _now_iso())),
    ])
    return {"success": True, "balance": new_balance}

"""
BACKEND/services/transfer_service.py
--------------------------------------
Business logic for peer-to-peer transfers between customers.

Flow:
  1. Validate amount (positive, <= MAX)
  2. Verify sender's 4-digit PIN with check_password_hash
  3. Resolve recipient username -> customer row
  4. Check sender has sufficient funds
  5. Atomically: debit sender, credit recipient, log two transaction rows
"""

import logging
from datetime import datetime, timezone
from werkzeug.security import check_password_hash
from database.db import get_one, execute_transaction

logger = logging.getLogger(__name__)

MAX_TRANSFER_AMOUNT = 10_000.00   # per-transaction ceiling for transfers


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def transfer(sender_id: int, recipient_username: str, raw_amount, pin: str) -> dict:
    """
    Transfer *raw_amount* from *sender_id* to the customer identified by
    *recipient_username*, authorised by *pin*.

    Returns:
        {"success": True,  "balance": sender_new_balance, "recipient_name": str}
        {"success": False, "error": error_message}
    """

    # ── 1. Validate amount ────────────────────────────────────────────────────
    if raw_amount is None or str(raw_amount).strip() == "":
        return {"success": False, "error": "Amount is required."}
    try:
        amount = float(str(raw_amount).strip())
    except ValueError:
        return {"success": False, "error": "Please enter a valid numeric amount."}

    if amount <= 0:
        return {"success": False, "error": "Transfer amount must be greater than zero."}

    if amount > MAX_TRANSFER_AMOUNT:
        return {"success": False, "error": f"Transfer amount cannot exceed £{MAX_TRANSFER_AMOUNT:,.2f}."}

    # ── 2. Validate PIN ───────────────────────────────────────────────────────
    if not pin or not pin.strip():
        return {"success": False, "error": "PIN is required."}

    sender = get_one(
        "SELECT id, username, full_name, balance, pin_hash FROM customers WHERE id = ?",
        (sender_id,)
    )
    if sender is None:
        return {"success": False, "error": "Sender account not found."}

    if not sender.get("pin_hash") or not check_password_hash(sender["pin_hash"], pin.strip()):
        logger.warning("Invalid PIN attempt for customer_id=%s", sender_id)
        return {"success": False, "error": "Incorrect PIN. Please try again."}

    # ── 3. Resolve recipient ──────────────────────────────────────────────────
    if not recipient_username or not recipient_username.strip():
        return {"success": False, "error": "Recipient username is required."}

    recipient_username = recipient_username.strip().lower()

    if recipient_username == sender["username"].lower():
        return {"success": False, "error": "You cannot transfer money to yourself."}

    recipient = get_one(
        "SELECT id, username, full_name, balance FROM customers WHERE LOWER(username) = ?",
        (recipient_username,)
    )
    if recipient is None:
        return {"success": False, "error": f"No account found for username '{recipient_username}'."}

    # ── 4. Check sender balance ───────────────────────────────────────────────
    if sender["balance"] < amount:
        return {
            "success": False,
            "error": f"Insufficient funds. Your balance is £{sender['balance']:,.2f}.",
        }

    # ── 5. Atomic debit + credit + two transaction log rows ───────────────────
    sender_new_balance    = sender["balance"] - amount
    recipient_new_balance = recipient["balance"] + amount
    now                   = _now_iso()

    execute_transaction([
        (
            "UPDATE customers SET balance = ? WHERE id = ?",
            (sender_new_balance, sender_id),
        ),
        (
            "UPDATE customers SET balance = ? WHERE id = ?",
            (recipient_new_balance, recipient["id"]),
        ),
        (
            "INSERT INTO transactions (customer_id, type, amount, timestamp, related_user) VALUES (?,?,?,?,?)",
            (sender_id, "transfer_out", amount, now, recipient["username"]),
        ),
        (
            "INSERT INTO transactions (customer_id, type, amount, timestamp, related_user) VALUES (?,?,?,?,?)",
            (recipient["id"], "transfer_in", amount, now, sender["username"]),
        ),
    ])

    logger.info(
        "Transfer: from=%s  to=%s  amount=%.2f  sender_balance=%.2f",
        sender["username"], recipient["username"], amount, sender_new_balance,
    )

    return {
        "success":        True,
        "balance":        sender_new_balance,
        "recipient_name": recipient["full_name"],
    }


def lookup_recipient(username: str) -> dict | None:
    """
    Return {"username": ..., "full_name": ...} for a given username,
    or None if not found. Used for live recipient name preview.
    """
    if not username or not username.strip():
        return None
    row = get_one(
        "SELECT username, full_name FROM customers WHERE LOWER(username) = ?",
        (username.strip().lower(),)
    )
    return row

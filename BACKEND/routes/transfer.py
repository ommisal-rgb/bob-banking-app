"""
BACKEND/routes/transfer.py
---------------------------
Blueprint: transfer
URL prefix: /

GET  /transfer          — show the send-money form
POST /transfer          — process a transfer
GET  /transfer/lookup   — JSON endpoint: resolve a username to a display name (live preview)
"""

import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from routes.auth import login_required
from services.transfer_service import transfer, lookup_recipient

logger = logging.getLogger(__name__)

transfer_bp = Blueprint("transfer", __name__)


@transfer_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer_route():
    if request.method == "GET":
        return render_template("transfer.html")

    sender_id          = session["user_id"]
    recipient_username = request.form.get("recipient", "").strip()
    raw_amount         = request.form.get("amount", "").strip()
    pin                = request.form.get("pin", "").strip()

    result = transfer(sender_id, recipient_username, raw_amount, pin)

    if result["success"]:
        flash(
            f"Transfer successful! £{float(raw_amount):,.2f} sent to "
            f"{result['recipient_name']}. Your new balance: £{result['balance']:,.2f}",
            "success",
        )
        return redirect(url_for("dashboard.dashboard"))

    # Stay on form and preserve non-sensitive inputs (never re-populate PIN)
    flash(result["error"], "danger")
    return render_template(
        "transfer.html",
        recipient=recipient_username,
        amount=raw_amount,
    ), 422


@transfer_bp.route("/transfer/lookup")
@login_required
def recipient_lookup():
    """
    JSON endpoint for live recipient name preview.
    Called by the transfer form as the user types a username.
    Returns: {"found": true, "full_name": "Alice Smith"} or {"found": false}
    """
    username = request.args.get("username", "").strip()
    sender_id = session["user_id"]

    if not username:
        return jsonify({"found": False})

    row = lookup_recipient(username)

    # Don't reveal the sender's own name (can't send to yourself)
    if row is None or row["username"].lower() == _get_sender_username(sender_id):
        return jsonify({"found": False})

    return jsonify({"found": True, "full_name": row["full_name"]})


def _get_sender_username(customer_id: int) -> str:
    from services.account_service import get_account
    acc = get_account(customer_id)
    return acc["username"].lower() if acc else ""

"""
BACKEND/routes/transactions.py
--------------------------------
Blueprint: transactions
URL prefix: /

Handles deposit and withdrawal form display and processing.
"""

import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
from routes.auth import login_required
from services.account_service import deposit, withdraw

logger = logging.getLogger(__name__)

transactions_bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------

@transactions_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit_route():
    if request.method == "GET":
        return render_template("deposit.html")

    customer_id = session["user_id"]
    raw_amount  = request.form.get("amount", "").strip()

    result = deposit(customer_id, raw_amount)

    if result["success"]:
        flash(f"Deposit successful! New balance: £{result['balance']:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard"))

    # Validation/business-logic error — stay on form.
    flash(result["error"], "danger")
    return render_template("deposit.html", amount=raw_amount), 422


# ---------------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------------

@transactions_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw_route():
    if request.method == "GET":
        return render_template("withdraw.html")

    customer_id = session["user_id"]
    raw_amount  = request.form.get("amount", "").strip()

    result = withdraw(customer_id, raw_amount)

    if result["success"]:
        flash(f"Withdrawal successful! New balance: £{result['balance']:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard"))

    flash(result["error"], "danger")
    return render_template("withdraw.html", amount=raw_amount), 422

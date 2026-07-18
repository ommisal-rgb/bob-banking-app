"""
BACKEND/routes/dashboard.py
-----------------------------
Blueprint: dashboard
URL prefix: /

Serves the account dashboard (read-only summary page).
"""

import logging
from flask import Blueprint, render_template, session
from routes.auth import login_required
from services.account_service import get_account, get_transactions

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    customer_id = session["user_id"]
    account = get_account(customer_id)
    recent_txns = get_transactions(customer_id)[:10]  # show last 10 transactions

    return render_template(
        "dashboard.html",
        full_name=account["full_name"],
        balance=account["balance"],
        transactions=recent_txns,
    )

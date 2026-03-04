"""
Reporting and branch-level helpers.

Implements higher-level reporting logic on top of `db_helpers`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from db import fetch_one, fetch_all
from . import db_helpers


def get_branch_report(branch_id: int) -> Dict[str, Any]:
    """
    (22) Aggregate report for a branch.

    Returns a dict with keys such as:
    - branch
    - total_customers
    - total_accounts
    - total_balance
    - active_loans
    - pending_loans
    - total_cards
    """
    branch = db_helpers.get_branch_by_id(branch_id)

    totals = fetch_one(
        """
        SELECT
            COUNT(DISTINCT a.account_id) AS total_accounts,
            COUNT(DISTINCT a.customer_id) AS total_customers,
            COALESCE(SUM(a.balance), 0) AS total_balance
        FROM accounts a
        WHERE a.branch_id = %s
        """,
        (branch_id,),
    )

    loan_counts = fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status IN ('ACTIVE', 'APPROVED')) AS active_loans,
            COUNT(*) FILTER (WHERE status = 'PENDING') AS pending_loans
        FROM loans
        WHERE branch_id = %s
        """,
        (branch_id,),
    )

    card_counts = fetch_one(
        """
        SELECT COUNT(*) AS total_cards
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        WHERE a.branch_id = %s
        """,
        (branch_id,),
    )

    return {
        "branch": branch,
        "total_accounts": totals["total_accounts"] if totals else 0,
        "total_customers": totals["total_customers"] if totals else 0,
        "total_balance": totals["total_balance"] if totals else 0,
        "active_loans": loan_counts["active_loans"] if loan_counts else 0,
        "pending_loans": loan_counts["pending_loans"] if loan_counts else 0,
        "total_cards": card_counts["total_cards"] if card_counts else 0,
    }


def get_all_transactions(branch_id: int, filters: dict | None = None) -> List[Dict[str, Any]]:
    """
    (23) Thin wrapper around db_helpers.get_all_transactions for clarity.
    """
    return db_helpers.get_all_transactions(branch_id, filters)


def get_branch_transactions(branch_id: int, filters: dict | None = None) -> List[Dict[str, Any]]:
    """
    Used by the `/employee/transactions` route to render the
    transaction monitoring view.
    """
    return get_all_transactions(branch_id, filters)


def get_employee_dashboard_summary(employee_id: int, branch_id: int) -> Dict[str, Any]:
    """
    Convenience summary for the employee dashboard.
    """
    from . import employee_loans_cards
    branch_report = get_branch_report(branch_id)

    my_loan_actions = fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'APPROVED') AS approved,
            COUNT(*) FILTER (WHERE status = 'REJECTED') AS rejected
        FROM loans
        WHERE employee_id = %s
        """,
        (employee_id,),
    )

    recent_customers = fetch_all(
        """
        SELECT c.*
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        WHERE a.branch_id = %s
        GROUP BY c.customer_id
        ORDER BY c.created_at DESC
        LIMIT 5
        """,
        (branch_id,),
    )

    # Fetch pending items for the dashboard
    pending_loans = employee_loans_cards.get_pending_loans(branch_id)
    pending_cards = employee_loans_cards.get_card_requests(branch_id)

    return {
        "branch": branch_report.get("branch"),
        "totals": branch_report,
        "my_loan_actions": my_loan_actions or {"approved": 0, "rejected": 0},
        "recent_customers": recent_customers,
        "pending_loans": pending_loans,
        "pending_cards": pending_cards,
    }


"""
Customer core operations (functions 1–5).

These functions encapsulate login, dashboard aggregation and basic
customer-facing data fetches.
"""

from __future__ import annotations

import bcrypt
from typing import Any, Dict, List, Optional, Tuple

from db import fetch_one, fetch_all, get_cursor


def verify_customer_login(mobile: str, password: str) -> Optional[Dict[str, Any]]:
    """
    (1) Verify customer login.
    For customer_id <= 12, allow plain text comparison.
    For others, use bcrypt hashing.
    """
    customer = fetch_one(
        "SELECT * FROM customers WHERE mobile = %s",
        (mobile,),
    )
    if not customer:
        return None

    stored = customer.get("password_hash")
    if not stored:
        return None

    customer_id = customer["customer_id"]
    
    # Per user request: let the customer_id <= 12 do fine with plain passwords
    if customer_id <= 12:
        # Check plain text first
        if password == stored:
            success = True
        else:
            # Also try bcrypt just in case it was already hashed
            try:
                success = bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
            except Exception:
                success = False
    else:
        # For new/other customers, strictly use bcrypt
        try:
            success = bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            success = False

    if success:
        # Do not leak the hash further in the app
        customer_data = dict(customer)
        customer_data.pop("password_hash", None)
        return customer_data

    return None


def get_customer_by_mobile(mobile: str) -> Optional[Dict[str, Any]]:
    """Fetch a customer by mobile number."""
    return fetch_one(
        "SELECT * FROM customers WHERE mobile = %s",
        (mobile,),
    )


def create_customer(
    first_name: str,
    last_name: str,
    dob: str,
    email: str,
    mobile: str,
    password: str,
) -> Dict[str, Any]:
    """
    Create a new customer with a hashed password.
    """
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Use an explicit transaction with commit so the new customer is persisted.
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO customers (first_name, last_name, dob, email, mobile, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (first_name, last_name, dob, email, mobile, hashed_password),
        )
        row = cur.fetchone()

    return row


def get_customer_profile(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    (3) Fetch basic customer profile details.
    """
    return fetch_one(
        "SELECT * FROM customers WHERE customer_id = %s",
        (customer_id,),
    )


def get_customer_accounts(customer_id: int) -> List[Dict[str, Any]]:
    """
    (5) Fetch all accounts that belong to a customer.
    """
    return fetch_all(
        """
        SELECT
            a.*,
            b.branch_name,
            b.ifsc_code
        FROM accounts a
        JOIN branches b ON a.branch_id = b.branch_id
        WHERE a.customer_id = %s
          AND a.status = 'active'
        ORDER BY a.opened_at ASC
        """,
        (customer_id,),
    )


def get_transaction_history(
    account_id: int,
    limit: int = 50,
    date_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    (4) Get transaction history for an account.
    """
    params: list[Any] = [account_id]
    where_clauses = ["t.account_id = %s"]

    if date_filter:
        where_clauses.append("t.created_at::date >= %s")
        params.append(date_filter)

    params.append(limit)

    sql = f"""
        SELECT
            t.tx_id,
            t.tx_type,
            t.amount,
            t.balance_after,
            t.related_account,
            a_rel.account_number as related_account_number,
            a_own.account_number as own_account_number,
            t.created_at,
            t.description
        FROM transactions t
        JOIN accounts a_own ON t.account_id = a_own.account_id
        LEFT JOIN accounts a_rel ON t.related_account = a_rel.account_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY t.created_at DESC, t.tx_id DESC
        LIMIT %s
    """

    return fetch_all(sql, tuple(params))


def get_all_customer_transactions(
    customer_id: int,
    limit: int = 50,
    date_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch transactions for all accounts belonging to a customer.
    """
    params: list[Any] = [customer_id]
    where_clauses = ["a_own.customer_id = %s"]

    if date_filter:
        where_clauses.append("t.created_at::date >= %s")
        params.append(date_filter)

    params.append(limit)

    sql = f"""
        SELECT
            t.tx_id,
            t.tx_type,
            t.amount,
            t.balance_after,
            t.related_account,
            a_rel.account_number as related_account_number,
            a_own.account_number as own_account_number,
            t.created_at,
            t.description
        FROM transactions t
        JOIN accounts a_own ON t.account_id = a_own.account_id
        LEFT JOIN accounts a_rel ON t.related_account = a_rel.account_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY t.created_at DESC, t.tx_id DESC
        LIMIT %s
    """

    return fetch_all(sql, tuple(params))


def get_customer_dashboard(customer_id: int) -> Dict[str, Any]:
    """
    (2) Return a dashboard summary for the customer.

    Includes:
    - total_accounts
    - total_balance
    - active_loans
    - cards_count
    - recent_transactions (last 5 across all accounts)
    """
    accounts = get_customer_accounts(customer_id)
    total_accounts = len(accounts)
    total_balance = sum(a["balance"] for a in accounts) if accounts else 0

    loans = fetch_all(
        "SELECT * FROM loans WHERE customer_id = %s AND status IN ('ACTIVE', 'PENDING')",
        (customer_id,),
    )
    cards = fetch_all(
        """
        SELECT c.*
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        WHERE a.customer_id = %s
        """,
        (customer_id,),
    )

    recent_tx = fetch_all(
        """
        SELECT
            t.tx_id,
            t.account_id,
            a.account_number,
            t.tx_type,
            t.amount,
            t.balance_after,
            t.created_at,
            t.description
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.customer_id = %s
        ORDER BY t.created_at DESC, t.tx_id DESC
        LIMIT 5
        """,
        (customer_id,),
    )

    return {
        "total_accounts": total_accounts,
        "total_balance": total_balance,
        "active_loans": len(loans),
        "cards_count": len(cards),
        "recent_transactions": recent_tx,
    }


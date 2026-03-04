"""
DB helper functions for common lookups and validations.

These correspond to the shared helper responsibilities (functions 24–32).
They are intentionally small, reusable primitives that other modules import.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from db import fetch_one, fetch_all, execute, get_cursor


def get_account_by_id(account_id: int) -> Optional[Dict[str, Any]]:
    """(24) Get a single account row by its numeric ID."""
    return fetch_one(
        "SELECT * FROM accounts WHERE account_id = %s",
        (account_id,),
    )


def get_account_balance(account_id: int) -> Optional[Decimal]:
    """(25) Return the current balance for an account, or None if missing."""
    row = fetch_one(
        "SELECT balance FROM accounts WHERE account_id = %s",
        (account_id,),
    )
    if not row:
        return None
    return row["balance"]


def update_account_balance(account_id: int, new_balance: Decimal) -> None:
    """(26) Persist a new balance for an account."""
    execute(
        "UPDATE accounts SET balance = %s WHERE account_id = %s",
        (new_balance, account_id),
    )


def set_account_status(account_id: int, status: str) -> None:
    """
    Soft-delete or change status of an account.

    Example statuses (based on schema): 'active', 'closed', etc.
    """
    execute(
        "UPDATE accounts SET status = %s WHERE account_id = %s",
        (status, account_id),
    )


def has_outstanding_loans(account_id: int) -> bool:
    """
    Check if an account has any outstanding or pending loans.
    """
    row = fetch_one(
        "SELECT COUNT(*) as count FROM loans WHERE linked_account_id = %s AND status IN ('PENDING', 'APPROVED', 'ACTIVE')",
        (account_id,),
    )
    return (row["count"] if row else 0) > 0


def create_account(
    customer_id: int,
    branch_id: int,
    account_type: str,
    currency: str,
) -> Dict[str, Any]:
    """
    Create a new account for a customer with an initial balance of 0.
    """
    # Simple account number generator: BRANCHID + CUSTOMERID + timestamp-based suffix
    import time

    suffix = int(time.time() * 1000) % 10_000_000
    account_number = f"ACC{branch_id:03d}{customer_id:05d}{suffix:07d}"[:20]

    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO accounts (
                customer_id,
                branch_id,
                account_number,
                balance,
                account_type,
                currency
            )
            VALUES (%s, %s, %s, 0.0, %s, %s)
            RETURNING *
            """,
            (
                customer_id,
                branch_id,
                account_number,
                account_type,
                currency,
            ),
        )
        row = cur.fetchone()

    return row


def get_all_branches() -> List[Dict[str, Any]]:
    """Return all branches for use in dropdowns."""
    return fetch_all(
        "SELECT * FROM branches ORDER BY branch_name ASC, branch_id ASC",
        (),
    )


def create_transaction(
    account_id: int,
    tx_type: str,
    amount: Decimal,
    related_account: Optional[int],
    description: str,
    cursor=None,
) -> None:
    """
    (27) Insert a transaction row and update balance_after.

    If `cursor` is provided, it is assumed to be part of an existing
    transaction (e.g. a transfer). Otherwise this function manages its
    own connection/transaction.
    """
    def _do_insert(cur):
        cur.execute(
            "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
            (account_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Account {account_id} not found")

        current_balance = row["balance"]
        # Interpret tx_type semantics for sign – very simple model
        sign = -1 if tx_type.upper() in {"WITHDRAWAL", "DEBIT", "TRANSFER_OUT"} else 1
        new_balance = current_balance + (sign * amount)

        cur.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
            """,
            (new_balance, account_id),
        )

        cur.execute(
            """
            INSERT INTO transactions (
                account_id, tx_type, amount, balance_after, related_account, description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (account_id, tx_type, amount, new_balance, related_account, description),
        )

    if cursor is not None:
        _do_insert(cursor)
    else:
        with get_cursor(commit=True) as cur:
            _do_insert(cur)


def manual_deposit(account_id: int, amount: Decimal, description: str) -> bool:
    """
    Perform a manual deposit into an account (e.g., by an admin for a cheque).
    Ensures the transaction is reflected in the transactions table and account balance.
    """
    try:
        with get_cursor(commit=True) as cur:
            # Lock the account row
            cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
            row = cur.fetchone()
            if not row:
                return False

            current_balance = row["balance"]
            new_balance = current_balance + amount

            # Update balance
            cur.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (new_balance, account_id)
            )

            # Insert transaction record
            cur.execute(
                """
                INSERT INTO transactions (
                    account_id, tx_type, amount, balance_after, description
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (account_id, 'DEPOSIT', amount, new_balance, description)
            )
        return True
    except Exception:
        return False

def get_loan_by_id(loan_id: int) -> Optional[Dict[str, Any]]:
    """(28) Fetch a single loan by ID."""
    return fetch_one(
        "SELECT * FROM loans WHERE loan_id = %s",
        (loan_id,),
    )


def get_branch_by_id(branch_id: int) -> Optional[Dict[str, Any]]:
    """(29) Fetch a branch row."""
    return fetch_one(
        "SELECT * FROM branches WHERE branch_id = %s",
        (branch_id,),
    )


def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
    """(30) Fetch an employee row."""
    return fetch_one(
        "SELECT * FROM employees WHERE employee_id = %s",
        (employee_id,),
    )


def validate_account_exists(account_number: str) -> bool:
    """
    (31) Check if an account number exists.

    Note: This uses the `account_number` column, which is distinct
    from the internal numeric `account_id`.
    """
    row = fetch_one(
        "SELECT 1 FROM accounts WHERE account_number = %s",
        (account_number,),
    )
    return row is not None


def check_sufficient_balance(account_id: int, amount: Decimal) -> bool:
    """
    (32) Return True if the account has at least `amount` available.
    """
    balance = get_account_balance(account_id)
    if balance is None:
        return False
    # Convert to Decimal for safe comparison
    required = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    return balance >= required


def get_all_transactions(branch_id: int, filters: dict | None = None) -> List[Dict[str, Any]]:
    """
    Helper used by reporting (23).

    Returns all transactions for accounts belonging to a branch,
    with optional filters (account_id, tx_type).
    """
    filters = filters or {}
    params: list[Any] = [branch_id]
    where_clauses = ["a.branch_id = %s"]

    if filters.get("account_id"):
        where_clauses.append("t.account_id = %s")
        params.append(filters["account_id"])

    if filters.get("tx_type"):
        where_clauses.append("t.tx_type = %s")
        params.append(filters["tx_type"])

    sql = f"""
        SELECT
            t.tx_id,
            t.account_id,
            a.account_number,
            t.tx_type,
            t.amount,
            t.balance_after,
            t.related_account,
            t.created_at,
            t.description
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY t.created_at DESC, t.tx_id DESC
    """

    return fetch_all(sql, tuple(params))


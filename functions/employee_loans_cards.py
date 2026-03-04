"""
Employee loan and card management (functions 16–21).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import random

from db import fetch_one, fetch_all, execute, get_cursor
from . import db_helpers


def get_pending_loans(branch_id: int) -> List[Dict[str, Any]]:
    """
    (16) Get all pending loans for a branch.
    """
    return fetch_all(
        """
        SELECT
            l.*,
            c.first_name,
            c.last_name,
            a.account_number
        FROM loans l
        JOIN customers c ON l.customer_id = c.customer_id
        JOIN accounts a ON l.linked_account_id = a.account_id
        WHERE l.branch_id = %s AND l.status = 'PENDING'
        ORDER BY l.created_at ASC
        """,
        (branch_id,),
    )


def get_all_loans(branch_id: int, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    (17) Get all loans for a branch, optionally filtered by status.
    """
    params: list[Any] = [branch_id]
    where = ["l.branch_id = %s"]

    if status_filter:
        where.append("l.status = %s")
        params.append(status_filter)

    sql = f"""
        SELECT
            l.*,
            c.first_name,
            c.last_name,
            a.account_number
        FROM loans l
        JOIN customers c ON l.customer_id = c.customer_id
        JOIN accounts a ON l.linked_account_id = a.account_id
        WHERE {" AND ".join(where)}
        ORDER BY l.created_at DESC
    """

    return fetch_all(sql, tuple(params))


def approve_loan(loan_id: int, employee_id: int) -> bool:
    """
    (18) Approve a loan and disburse funds to the linked account.
    Returns True if successful, False otherwise.
    """
    with get_cursor(commit=True) as cur:
        # Lock and check loan status
        cur.execute(
            "SELECT * FROM loans WHERE loan_id = %s FOR UPDATE",
            (loan_id,),
        )
        loan = cur.fetchone()
        if not loan or loan["status"] != 'PENDING':
            return False

        # Lock the linked account
        account_id = loan["linked_account_id"]
        cur.execute(
            "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
            (account_id,),
        )
        account = cur.fetchone()
        if not account:
            return False

        current_balance = account["balance"]
        principal = loan["principal_amount"]
        new_balance = current_balance + principal

        # Update account balance
        cur.execute(
            "UPDATE accounts SET balance = %s WHERE account_id = %s",
            (new_balance, account_id),
        )

        # Insert a transaction for loan disbursement
        cur.execute(
            """
            INSERT INTO transactions (
                account_id, tx_type, amount, balance_after, related_account, description
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                account_id,
                "CREDIT",
                principal,
                new_balance,
                None,
                f"Loan disbursement #{loan['loan_number']}",
            ),
        )

        # Mark loan as ACTIVE and set employee / disbursement date
        cur.execute(
            """
            UPDATE loans
            SET status = 'ACTIVE',
                employee_id = %s,
                disbursement_date = CURRENT_DATE
            WHERE loan_id = %s
            """,
            (employee_id, loan_id),
        )
        
        return True


def reject_loan(loan_id: int, employee_id: int) -> bool:
    """
    (19) Reject a loan.
    """
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT status FROM loans WHERE loan_id = %s FOR UPDATE", (loan_id,))
        loan = cur.fetchone()
        if not loan or loan["status"] != 'PENDING':
            return False

        cur.execute(
            """
            UPDATE loans
            SET status = 'REJECTED',
                employee_id = %s
            WHERE loan_id = %s
            """,
            (employee_id, loan_id),
        )
        return True


def _generate_card_number() -> str:
    """Generate a pseudo-random 16-digit card number."""
    return "".join(str(random.randint(0, 9)) for _ in range(16))


def _generate_cvv() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(3))


def issue_new_card(
    account_id: int,
    card_type: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    (20) Issue a new card for an account.
    """
    card_number = _generate_card_number()
    cvv = _generate_cvv()

    # Default expiry: 4 years from today
    expiry = date.today().replace(year=date.today().year + 4)

    credit_limit = data.get("credit_limit")
    withdrawal_limit = data.get("withdrawal_limit")

    row = fetch_one(
        """
        INSERT INTO cards (
            account_id, card_number, card_type,
            expiry_date, cvv,
            credit_limit, withdrawal_limit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            account_id,
            card_number,
            card_type,
            expiry,
            cvv,
            credit_limit,
            withdrawal_limit,
        ),
    )
    return row


def get_all_cards(branch_id: int) -> List[Dict[str, Any]]:
    """
    (21) Get all cards for accounts within a branch.
    """
    return fetch_all(
        """
        SELECT
            c.*,
            a.account_number,
            a.account_type
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        WHERE a.branch_id = %s
        ORDER BY c.issued_date DESC
        """,
        (branch_id,),
    )


def get_card_requests(branch_id: int) -> List[Dict[str, Any]]:
    """
    Find all card requests (withdrawal_limit = -1) for a branch.
    """
    return fetch_all(
        """
        SELECT
            c.*,
            a.account_number,
            cu.first_name,
            cu.last_name
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        JOIN customers cu ON a.customer_id = cu.customer_id
        WHERE a.branch_id = %s AND c.withdrawal_limit = -1
        ORDER BY c.issued_date ASC
        """,
        (branch_id,),
    )


def approve_card_request(
    card_id: int,
    credit_limit: float,
    withdrawal_limit: float,
) -> bool:
    """
    Approve a card request: generate real number/cvv, set limits, set status to Active.
    """
    with get_cursor(commit=True) as cur:
        # Check if it's still a pending request
        cur.execute("SELECT withdrawal_limit FROM cards WHERE card_id = %s FOR UPDATE", (card_id,))
        card = cur.fetchone()
        if not card or card["withdrawal_limit"] != -1:
            return False

        card_number = _generate_card_number()
        cvv = _generate_cvv()
        expiry = date.today().replace(year=date.today().year + 4)

        cur.execute(
            """
            UPDATE cards
            SET card_number = %s,
                cvv = %s,
                expiry_date = %s,
                status = 'Active',
                credit_limit = %s,
                withdrawal_limit = %s
            WHERE card_id = %s
            """,
            (card_number, cvv, expiry, credit_limit, withdrawal_limit, card_id)
        )
        return True


def reject_card_request(card_id: int) -> bool:
    """
    Reject a card request by deleting the temporary record.
    """
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT withdrawal_limit FROM cards WHERE card_id = %s FOR UPDATE", (card_id,))
        card = cur.fetchone()
        if not card or card["withdrawal_limit"] != -1:
            return False

        cur.execute("DELETE FROM cards WHERE card_id = %s", (card_id,))
        return True


"""
Extended customer operations (functions 6–10).

Includes money transfers, loans, cards, and account statements.
"""

from __future__ import annotations

import csv
import os
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from db import get_cursor, fetch_all, fetch_one, execute
from . import db_helpers


def transfer_money(
    from_account: int,
    to_account_number: str,
    amount: float,
    description: str = "Transfer",
) -> Tuple[bool, str]:
    """
    (6) Transfer money from a source account ID to a destination account number.

    Performs basic validations and a single DB transaction that:
    - resolves to_account_number to to_account_id
    - locks both accounts
    - checks sufficient balance
    - updates balances
    - inserts two transaction rows (debit and credit)
    """
    amt = Decimal(str(amount))
    if amt <= 0:
        return False, "Amount must be positive."

    if not db_helpers.check_sufficient_balance(from_account, amt):
        return False, "Insufficient balance."

    with get_cursor(commit=True) as cur:
        # Resolve destination account number
        cur.execute("SELECT account_id FROM accounts WHERE account_number = %s", (to_account_number,))
        to_row = cur.fetchone()
        if not to_row:
            return False, f"Destination account '{to_account_number}' not found."
        
        to_account = to_row["account_id"]

        if from_account == to_account:
            return False, "Source and destination accounts must be different."

        # Lock both accounts in a deterministic order to avoid deadlocks
        acc_ids = sorted([from_account, to_account])
        cur.execute(
            """
            SELECT account_id, balance
            FROM accounts
            WHERE account_id = ANY(%s)
            FOR UPDATE
            """,
            (acc_ids,),
        )
        rows = {row["account_id"]: row for row in cur.fetchall()}

        if from_account not in rows or to_account not in rows:
            raise ValueError("One or both accounts not found after lock.")

        from_balance = rows[from_account]["balance"]
        to_balance = rows[to_account]["balance"]

        if from_balance < amt:
            return False, "Insufficient balance."

        new_from_balance = from_balance - amt
        new_to_balance = to_balance + amt

        # Update balances
        cur.execute(
            "UPDATE accounts SET balance = %s WHERE account_id = %s",
            (new_from_balance, from_account),
        )
        cur.execute(
            "UPDATE accounts SET balance = %s WHERE account_id = %s",
            (new_to_balance, to_account),
        )

        # Insert transactions
        cur.execute(
            """
            INSERT INTO transactions (
                account_id, tx_type, amount, balance_after, related_account, description
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (from_account, "DEBIT", amt, new_from_balance, to_account, description),
        )
        cur.execute(
            """
            INSERT INTO transactions (
                account_id, tx_type, amount, balance_after, related_account, description
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (to_account, "CREDIT", amt, new_to_balance, from_account, description),
        )

    return True, "Transfer completed successfully."


def get_customer_loans(customer_id: int) -> List[Dict[str, Any]]:
    """
    (7) Fetch all loans belonging to a customer.
    """
    return fetch_all(
        """
        SELECT
            l.*,
            a.account_number,
            b.branch_name
        FROM loans l
        JOIN accounts a ON l.linked_account_id = a.account_id
        JOIN branches b ON l.branch_id = b.branch_id
        WHERE l.customer_id = %s
        ORDER BY l.created_at DESC
        """,
        (customer_id,),
    )


def get_customer_cards(customer_id: int) -> List[Dict[str, Any]]:
    """
    (9) Fetch all cards linked to a customer's accounts.
    """
    return fetch_all(
        """
        SELECT
            c.*,
            a.account_number,
            a.account_type
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        JOIN customers cu ON a.customer_id = cu.customer_id
        WHERE cu.customer_id = %s
        ORDER BY c.issued_date DESC
        """,
        (customer_id,),
    )


def request_card(account_id: int, card_type: str) -> Tuple[bool, str]:
    """
    Submit a card request by creating a 'Blocked' card with a temporary number.
    Uses withdrawal_limit = -1 as a flag for 'PENDING APPROVAL'.
    """
    import time
    from datetime import date
    
    # Check if a request already exists for this account and type
    existing = fetch_one(
        "SELECT 1 FROM cards WHERE account_id = %s AND card_type = %s AND withdrawal_limit = -1",
        (account_id, card_type)
    )
    if existing:
        return False, f"A {card_type} card request is already pending for this account."

    # Temporary card number: REQ + timestamp
    temp_card_number = f"REQ{int(time.time())}"[:16]
    cvv = "000"
    expiry = date.today()

    try:
        execute(
            """
            INSERT INTO cards (
                account_id, card_number, card_type, 
                expiry_date, cvv, status, 
                credit_limit, withdrawal_limit
            ) VALUES (%s, %s, %s, %s, %s, 'Blocked', 0, -1)
            """,
            (account_id, temp_card_number, card_type, expiry, cvv)
        )
        return True, f"Request for {card_type} card submitted successfully."
    except Exception as e:
        return False, f"Failed to submit request: {str(e)}"


def _calculate_emi(principal: Decimal, annual_rate: float, tenure_months: int) -> Decimal:
    """Simple EMI calculation helper."""
    if tenure_months <= 0:
        return Decimal("0.01") # Minimal value to satisfy constraints if tenure is somehow 0

    monthly_rate = Decimal(str(annual_rate)) / Decimal("1200")
    if monthly_rate == 0:
        return (principal / tenure_months).quantize(Decimal("0.01"))

    # Use float math for simplicity
    p = float(principal)
    r = float(monthly_rate)
    n = tenure_months
    emi = p * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return Decimal(str(round(emi, 2)))


def request_loan(
    customer_id: int,
    account_id: int,
    loan_type: str,
    principal_amount: float,
    tenure_months: int,
) -> Tuple[bool, str]:
    """
    Create a new PENDING loan request for the customer.
    """
    # Validate account belongs to this customer
    account = fetch_one(
        "SELECT account_id, customer_id, branch_id FROM accounts WHERE account_id = %s",
        (account_id,),
    )
    if not account or account["customer_id"] != customer_id:
        return False, "Invalid account selected."

    if principal_amount <= 0 or tenure_months <= 0:
        return False, "Amount and tenure must be positive."

    principal = Decimal(str(principal_amount))

    # Basic interest-rate defaults by loan type
    rate_by_type = {
        "Personal": 12.0,
        "Home": 8.5,
        "Auto": 9.0,
        "Education": 9.0,
        "Business": 11.0,
    }
    interest_rate = rate_by_type.get(loan_type, 10.0)
    
    # Calculate EMI to satisfy database constraint CHECK (emi_amount > 0)
    emi_amount = _calculate_emi(principal, interest_rate, tenure_months)

    # Generate a simple unique-ish loan_number based on next ID
    next_row = fetch_one("SELECT COALESCE(MAX(loan_id), 0) + 1 AS next_id FROM loans")
    next_id = next_row["next_id"]
    loan_number = f"LN{int(next_id):010d}"

    # Use an explicit transaction with commit so the new loan persists
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO loans (
                customer_id,
                branch_id,
                linked_account_id,
                loan_number,
                loan_type,
                principal_amount,
                interest_rate,
                tenure_months,
                emi_amount,
                outstanding_balance,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
            RETURNING *
            """,
            (
                customer_id,
                account["branch_id"],
                account_id,
                loan_number,
                loan_type,
                principal,
                interest_rate,
                tenure_months,
                emi_amount,
                principal,
            ),
        )
        row = cur.fetchone()

    if not row:
        return False, "Could not create loan request."

    return True, "Loan request submitted successfully."

def get_customer_fds(customer_id: int) -> List[Dict[str, Any]]:
    """
    Fetch all fixed deposits belonging to a customer.
    """
    return fetch_all(
        """
        SELECT fd.*, a.account_number as linked_account_number
        FROM fixed_deposits fd
        JOIN accounts a ON fd.linked_account_id = a.account_id
        WHERE fd.customer_id = %s
        ORDER BY fd.start_date DESC
        """,
        (customer_id,),
    )

def withdraw_fd(fd_id: int, customer_id: int) -> Tuple[bool, str]:
    """
    Withdraw/Close a fixed deposit and transfer funds to the linked account.
    """
    with get_cursor(commit=True) as cur:
        # Lock FD row
        cur.execute("SELECT * FROM fixed_deposits WHERE fd_id = %s AND customer_id = %s FOR UPDATE", (fd_id, customer_id))
        fd = cur.fetchone()
        if not fd:
            return False, "Fixed Deposit not found."
        
        if fd["status"] != "ACTIVE":
            return False, f"Fixed Deposit is already {fd['status']}."

        linked_account_id = fd["linked_account_id"]
        # Determine if it's a regular maturity or premature closure
        is_matured = date.today() >= fd["maturity_date"]
        amount_to_transfer = fd["maturity_amount"] if is_matured else fd["principal_amount"]
        new_status = "MATURED" if is_matured else "PREMATURELY_CLOSED"

        # Lock Linked Account
        cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (linked_account_id,))
        account = cur.fetchone()
        if not account:
            return False, "Linked account not found."

        new_balance = account["balance"] + amount_to_transfer

        # 1. Update account balance
        cur.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, linked_account_id))

        # 2. Update FD status
        cur.execute("UPDATE fixed_deposits SET status = %s WHERE fd_id = %s", (new_status, fd_id))

        # 3. Insert Transaction
        description = f"FD Withdrawal: {fd['fd_number']} ({new_status})"
        cur.execute(
            """
            INSERT INTO transactions (
                account_id, tx_type, amount, balance_after, description
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (linked_account_id, "CREDIT", amount_to_transfer, new_balance, description)
        )

    return True, f"Fixed Deposit withdrawn successfully. {amount_to_transfer} INR credited to {account['account_number']}."

def generate_account_statement(
    account_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    export_to_csv: bool = False,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    (10) Generate an account statement (optionally as CSV).

    Returns (rows, csv_path). If `export_to_csv` is False, csv_path is None.
    """
    params: list[Any] = [account_id]
    where = ["t.account_id = %s"]

    if start_date:
        where.append("t.created_at::date >= %s")
        params.append(start_date)
    if end_date:
        where.append("t.created_at::date <= %s")
        params.append(end_date)

    sql = f"""
        SELECT
            t.tx_id,
            t.created_at,
            t.tx_type,
            t.amount,
            t.balance_after,
            t.related_account,
            t.description
        FROM transactions t
        WHERE {" AND ".join(where)}
        ORDER BY t.created_at ASC, t.tx_id ASC
    """

    rows = fetch_all(sql, tuple(params))

    csv_path: Optional[str] = None
    if export_to_csv:
        os.makedirs("statements", exist_ok=True)
        filename = f"statement_account_{account_id}.csv"
        csv_path = os.path.join("statements", filename)

        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Tx ID", "Date", "Type", "Amount", "Balance After", "Related Account", "Description"]
            )
            for r in rows:
                writer.writerow(
                    [
                        r["tx_id"],
                        r["created_at"],
                        r["tx_type"],
                        r["amount"],
                        r["balance_after"],
                        r["related_account"],
                        r["description"],
                    ]
                )

    return rows, csv_path


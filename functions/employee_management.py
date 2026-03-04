"""
Employee authentication and customer management (functions 11–15).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import bcrypt

from db import fetch_one, fetch_all, execute


def verify_employee_login(employee_id: str, password: str) -> Optional[Dict[str, Any]]:
    """
    (11) Verify employee login. 
    Accepts 'password' as the password for all employees.
    """
    try:
        emp_id_int = int(employee_id)
    except ValueError:
        return None

    employee = fetch_one(
        "SELECT * FROM employees WHERE employee_id = %s",
        (emp_id_int,),
    )
    if not employee:
        return None

    # Per user request: let the password 'password' login for employees
    if password != "password":
        return None

    employee_data = dict(employee)
    employee_data.pop("password_hash", None)
    return employee_data


def search_customers(query: str) -> List[Dict[str, Any]]:
    """
    (12) Search customers by name, email, or mobile.
    """
    like = f"%{query}%"
    return fetch_all(
        """
        SELECT
            c.customer_id,
            c.first_name,
            c.last_name,
            c.email,
            c.mobile,
            c.created_at
        FROM customers c
        WHERE
            c.first_name ILIKE %s OR
            c.last_name ILIKE %s OR
            c.email ILIKE %s OR
            c.mobile ILIKE %s
        ORDER BY c.created_at DESC
        """,
        (like, like, like, like),
    )


def get_customer_details(customer_id: int) -> Dict[str, Any]:
    """
    (13) Get full customer details for employee view.

    Returns a dict containing:
    - customer
    - accounts
    - loans
    - cards
    """
    customer = fetch_one(
        "SELECT * FROM customers WHERE customer_id = %s",
        (customer_id,),
    )

    accounts = fetch_all(
        """
        SELECT a.*, b.branch_name, b.ifsc_code
        FROM accounts a
        JOIN branches b ON a.branch_id = b.branch_id
        WHERE a.customer_id = %s
        ORDER BY a.opened_at ASC
        """,
        (customer_id,),
    )

    loans = fetch_all(
        "SELECT * FROM loans WHERE customer_id = %s ORDER BY created_at DESC",
        (customer_id,),
    )

    cards = fetch_all(
        """
        SELECT c.*, a.account_number
        FROM cards c
        JOIN accounts a ON c.account_id = a.account_id
        WHERE a.customer_id = %s
        """,
        (customer_id,),
    )

    return {
        "customer": customer,
        "accounts": accounts,
        "loans": loans,
        "cards": cards,
    }


def create_new_customer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    (14) Create a new customer.

    `data` is expected to contain first_name, last_name, dob, email, mobile.
    Returns the inserted customer row.
    """
    row = fetch_one(
        """
        INSERT INTO customers (first_name, last_name, dob, email, mobile)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            data.get("first_name"),
            data.get("last_name"),
            data.get("dob"),
            data.get("email"),
            data.get("mobile"),
        ),
    )
    return row


def create_new_account(
    customer_id: int,
    branch_id: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    (15) Create a new account for a customer at a branch.

    `data` can include:
    - account_type
    - currency
    """
    from functions import db_helpers

    account_type = data.get("account_type", "Savings")
    currency = data.get("currency", "INR")

    return db_helpers.create_account(
        customer_id=customer_id,
        branch_id=branch_id,
        account_type=account_type,
        currency=currency,
    )


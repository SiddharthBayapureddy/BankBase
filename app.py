import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
)
from dotenv import load_dotenv

from functions import (
    customer_core,
    customer_extended,
    employee_management,
    employee_loans_cards,
    db_helpers,
    reports,
)


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # -----------------------------
    # BASIC ROUTES
    # -----------------------------

    @app.route("/")
    def index():
        # Combined customer/employee login page
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    # -----------------------------
    # CUSTOMER AUTH + CORE
    # -----------------------------

    @app.route("/customer/signup", methods=["GET", "POST"])
    def customer_signup():
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            dob = request.form.get("dob", "").strip()
            email = request.form.get("email", "").strip()
            mobile = request.form.get("mobile", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return redirect(url_for("customer_signup"))

            if customer_core.get_customer_by_mobile(mobile):
                flash("A customer with this mobile already exists.", "error")
                return redirect(url_for("customer_signup"))

            customer = customer_core.create_customer(
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                email=email,
                mobile=mobile,
                password=password,
            )

            session["user_type"] = "customer"
            session["customer_id"] = customer["customer_id"]
            session["user_name"] = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Customer"
            flash("Account created successfully. Welcome!", "success")
            return redirect(url_for("customer_dashboard"))

        return render_template("customer_signup.html")

    @app.route("/customer/account/create", methods=["GET", 'POST'])
    def customer_create_account():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")

        if request.method == "POST":
            branch_id = int(request.form["branch_id"])
            account_type = request.form.get("account_type", "Savings")
            currency = request.form.get("currency", "INR")
            initial_deposit = float(request.form.get("initial_deposit") or 0)

            db_helpers.create_account(
                customer_id=customer_id,
                branch_id=branch_id,
                account_type=account_type,
                currency=currency,
                initial_deposit=initial_deposit,
            )
            flash("New account created successfully.", "success")
            return redirect(url_for("customer_dashboard"))

        branches = db_helpers.get_all_branches()
        return render_template("customer_create_account.html", branches=branches)

    @app.route("/customer/login", methods=["POST"])
    def customer_login():
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")

        customer = customer_core.verify_customer_login(mobile, password)
        if not customer:
            flash("Invalid mobile or password.", "error")
            return redirect(url_for("index"))

        session["user_type"] = "customer"
        session["customer_id"] = customer["customer_id"]
        session["user_name"] = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Customer"

        flash("Welcome back!", "success")
        return redirect(url_for("customer_dashboard"))

    @app.route("/customer/dashboard")
    def customer_dashboard():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        dashboard = customer_core.get_customer_dashboard(customer_id)
        profile = customer_core.get_customer_profile(customer_id)
        accounts = customer_core.get_customer_accounts(customer_id)

        return render_template(
            "customer_dashboard.html",
            dashboard=dashboard,
            profile=profile,
            accounts=accounts,
        )

    @app.route("/customer/account/<int:account_id>/close", methods=["POST"])
    def customer_close_account(account_id: int):
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        account = db_helpers.get_account_by_id(account_id)

        if not account or account["customer_id"] != customer_id:
            flash("Invalid account.", "error")
            return redirect(url_for("customer_dashboard"))

        # Prevent closing accounts with non-zero balance
        if account["balance"] != 0:
            flash("Please transfer or withdraw funds so balance is zero before closing the account.", "warning")
            return redirect(url_for("customer_dashboard"))

        db_helpers.set_account_status(account_id, "closed")
        flash("Account closed successfully.", "success")
        return redirect(url_for("customer_dashboard"))

    @app.route("/customer/transactions")
    def customer_transactions():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        account_id = request.args.get("account_id", type=int)
        limit = request.args.get("limit", default=50, type=int)
        date_filter = request.args.get("date_filter", default=None)

        if not account_id:
            flash("Please select an account to view transactions.", "warning")
            return redirect(url_for("customer_dashboard"))

        transactions = customer_core.get_transaction_history(
            account_id=account_id,
            limit=limit,
            date_filter=date_filter,
        )

        return render_template(
            "transaction_history.html",
            transactions=transactions,
            account_id=account_id,
        )

    @app.route("/customer/profile")
    def customer_profile():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        profile = customer_core.get_customer_profile(customer_id)
        accounts = customer_core.get_customer_accounts(customer_id)

        return render_template(
            "customer_details.html",
            profile=profile,
            accounts=accounts,
            readonly=True,
        )

    # -----------------------------
    # CUSTOMER TRANSFERS + LOANS/CARDS
    # -----------------------------

    @app.route("/customer/transfer", methods=["GET", "POST"])
    def customer_transfer():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        customer_accounts = customer_core.get_customer_accounts(customer_id)

        if request.method == "POST":
            from_account = int(request.form["from_account"])
            to_account = int(request.form["to_account"])
            amount = float(request.form["amount"])
            description = request.form.get("description", "Transfer")

            success, message = customer_extended.transfer_money(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                description=description,
            )
            flash(message, "success" if success else "error")
            if success:
                return redirect(url_for("customer_transactions", account_id=from_account))

        return render_template(
            "money_transfer.html",
            accounts=customer_accounts,
        )

    @app.route("/customer/loans")
    def customer_loans():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        loans = customer_extended.get_customer_loans(customer_id)
        accounts = customer_core.get_customer_accounts(customer_id)

        return render_template(
            "loans_dashboard.html",
            loans=loans,
            accounts=accounts,
        )

    @app.route("/customer/loans/request", methods=["POST"])
    def customer_request_loan():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        account_id = int(request.form["account_id"])
        loan_type = request.form["loan_type"]
        principal_amount = float(request.form["principal_amount"])
        tenure_months = int(request.form["tenure_months"])

        success, message = customer_extended.request_loan(
            customer_id=customer_id,
            account_id=account_id,
            loan_type=loan_type,
            principal_amount=principal_amount,
            tenure_months=tenure_months,
        )
        flash(message, "success" if success else "error")
        return redirect(url_for("customer_loans"))

    @app.route("/customer/loan/<int:loan_id>")
    def customer_loan_detail(loan_id: int):
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        loan = db_helpers.get_loan_by_id(loan_id)
        emi_schedule = customer_extended.get_loan_emi_schedule(loan_id)

        return render_template(
            "loan_emi_details.html",
            loan=loan,
            emi_schedule=emi_schedule,
        )

    @app.route("/customer/cards")
    def customer_cards():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        customer_id = session.get("customer_id")
        cards = customer_extended.get_customer_cards(customer_id)

        return render_template(
            "cards_list.html",
            cards=cards,
        )

    @app.route("/customer/statement")
    def customer_statement():
        if session.get("user_type") != "customer":
            return redirect(url_for("index"))

        account_id = request.args.get("account_id", type=int)
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        export = request.args.get("export", default="html")

        if not account_id:
            flash("Please choose an account.", "warning")
            return redirect(url_for("customer_dashboard"))

        start_date = datetime.fromisoformat(start_date_str).date() if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str).date() if end_date_str else None

        statement_rows, csv_path = customer_extended.generate_account_statement(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            export_to_csv=(export == "csv"),
        )

        if export == "csv" and csv_path:
            return send_file(csv_path, mimetype="text/csv", as_attachment=True)

        return render_template(
            "account_statement.html",
            rows=statement_rows,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

    # -----------------------------
    # EMPLOYEE AUTH + CUSTOMER MGMT
    # -----------------------------

    @app.route("/employee/login", methods=["POST"])
    def employee_login():
        employee_id = request.form.get("employee_id", "").strip()
        password = request.form.get("password", "")

        employee = employee_management.verify_employee_login(employee_id, password)
        if not employee:
            flash("Invalid employee ID or password.", "error")
            return redirect(url_for("index"))

        session["user_type"] = "employee"
        session["employee_id"] = employee["employee_id"]
        session["branch_id"] = employee["branch_id"]
        session["user_name"] = employee["name"]

        flash("Logged in as employee.", "success")
        return redirect(url_for("employee_dashboard"))

    @app.route("/employee/dashboard")
    def employee_dashboard():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        employee_id = session.get("employee_id")
        branch_id = session.get("branch_id")

        summary = reports.get_employee_dashboard_summary(employee_id, branch_id)

        return render_template(
            "employee_dashboard.html",
            summary=summary,
        )

    @app.route("/employee/search")
    def employee_search():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        query = request.args.get("q", "").strip()
        customers = employee_management.search_customers(query) if query else []

        return render_template(
            "customer_search.html",
            query=query,
            customers=customers,
        )

    @app.route("/employee/customer/<int:customer_id>")
    def employee_customer_detail(customer_id: int):
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        details = employee_management.get_customer_details(customer_id)

        return render_template(
            "customer_details.html",
            profile=details.get("customer"),
            accounts=details.get("accounts", []),
            loans=details.get("loans", []),
            cards=details.get("cards", []),
            readonly=False,
        )

    @app.route("/employee/account/create", methods=["GET", "POST"])
    def employee_create_account():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        branch_id = session.get("branch_id")

        if request.method == "POST":
            customer_id = int(request.form["customer_id"])
            data = {
                "account_type": request.form["account_type"],
                "currency": request.form.get("currency", "INR"),
                "initial_deposit": float(request.form.get("initial_deposit", 0)),
            }
            account = employee_management.create_new_account(
                customer_id=customer_id,
                branch_id=branch_id,
                data=data,
            )
            flash("Account created successfully.", "success")
            return redirect(url_for("employee_customer_detail", customer_id=customer_id))

        return render_template("create_account.html")

    # -----------------------------
    # EMPLOYEE LOAN & CARD MGMT
    # -----------------------------

    @app.route("/employee/loans")
    def employee_loans():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        branch_id = session.get("branch_id")
        status_filter = request.args.get("status", default=None)

        pending = employee_loans_cards.get_pending_loans(branch_id)
        all_loans = employee_loans_cards.get_all_loans(branch_id, status_filter=status_filter)

        return render_template(
            "loan_approval.html",
            pending_loans=pending,
            all_loans=all_loans,
        )

    @app.route("/employee/loans/approve/<int:loan_id>", methods=["POST"])
    def employee_approve_loan(loan_id: int):
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        employee_id = session.get("employee_id")
        employee_loans_cards.approve_loan(loan_id, employee_id)
        flash("Loan approved.", "success")
        return redirect(url_for("employee_loans"))

    @app.route("/employee/loans/reject/<int:loan_id>", methods=["POST"])
    def employee_reject_loan(loan_id: int):
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        employee_id = session.get("employee_id")
        employee_loans_cards.reject_loan(loan_id, employee_id)
        flash("Loan rejected.", "warning")
        return redirect(url_for("employee_loans"))

    @app.route("/employee/cards/issue", methods=["GET", "POST"])
    def employee_issue_card():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        if request.method == "POST":
            account_id = int(request.form["account_id"])
            card_type = request.form["card_type"]
            data = {
                "credit_limit": request.form.get("credit_limit"),
                "withdrawal_limit": request.form.get("withdrawal_limit"),
            }
            employee_loans_cards.issue_new_card(
                account_id=account_id,
                card_type=card_type,
                data=data,
            )
            flash("Card issued successfully.", "success")
            return redirect(url_for("employee_cards"))

        return render_template("issue_card.html")

    @app.route("/employee/cards")
    def employee_cards():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        branch_id = session.get("branch_id")
        cards = employee_loans_cards.get_all_cards(branch_id)

        return render_template(
            "cards_list.html",
            cards=cards,
        )

    # -----------------------------
    # REPORTS + HELPERS
    # -----------------------------

    @app.route("/employee/reports")
    def employee_reports():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        branch_id = session.get("branch_id")
        report = reports.get_branch_report(branch_id)

        return render_template(
            "branch_reports.html",
            report=report,
        )

    @app.route("/employee/transactions")
    def employee_transactions():
        if session.get("user_type") != "employee":
            return redirect(url_for("index"))

        branch_id = session.get("branch_id")
        filters = {
            "account_id": request.args.get("account_id", type=int),
            "tx_type": request.args.get("tx_type"),
        }

        transactions = reports.get_branch_transactions(branch_id, filters)

        return render_template(
            "transaction_monitoring.html",
            transactions=transactions,
            filters=filters,
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True)


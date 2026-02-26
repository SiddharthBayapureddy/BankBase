CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id) NOT NULL,
    branch_id INT REFERENCES branches(branch_id) NOT NULL,
    linked_account_id INT REFERENCES accounts(account_id) NOT NULL,
    loan_number VARCHAR(20) UNIQUE NOT NULL,
    loan_type VARCHAR(50) NOT NULL CHECK (loan_type IN ('Personal', 'Home', 'Auto', 'Education', 'Business')),
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    interest_rate NUMERIC(5, 2) NOT NULL CHECK (interest_rate > 0),
    tenure_months INT NOT NULL CHECK (tenure_months > 0),
    emi_amount NUMERIC(15, 2) NOT NULL CHECK (emi_amount > 0),
    outstanding_balance NUMERIC(15, 2) NOT NULL CHECK (outstanding_balance >= 0),
    disbursement_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('PENDING', 'APPROVED', 'ACTIVE', 'CLOSED', 'DEFAULTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
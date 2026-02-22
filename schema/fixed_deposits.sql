CREATE TABLE fixed_deposits (
    fd_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id) NOT NULL,
    linked_account_id INT REFERENCES accounts(account_id) NOT NULL, 
    fd_number VARCHAR(20) UNIQUE NOT NULL,
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    interest_rate NUMERIC(5, 2) NOT NULL CHECK (interest_rate > 0), 
    tenure_months INT NOT NULL CHECK (tenure_months > 0),
    start_date DATE DEFAULT CURRENT_DATE,
    maturity_date DATE NOT NULL,
    maturity_amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MATURED', 'PREMATURELY_CLOSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
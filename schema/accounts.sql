CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    branch_id INT REFERENCES branches(branch_id),
    account_number VARCHAR(20) UNIQUE,
    balance NUMERIC(15, 2) DEFAULT 0.00,
    account_type VARCHAR(20),
    currency VARCHAR(3) DEFAULT 'INR',
    status VARCHAR(10) DEFAULT 'active',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

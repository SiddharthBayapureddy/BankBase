CREATE TABLE transactions (
    tx_id SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(account_id), 
    tx_type VARCHAR(10) default 'TRANSFER', --ts is Like deposit or withdrawal or bank fee etc
    amount NUMERIC(15, 2) NOT NULL,
    balance_after NUMERIC(15, 2) NOT NULL,
    related_account INT REFERENCES(accounts(account_id)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(255) DEFAULT 'None'
    );
CREATE TABLE loan_emi (
    emi_id SERIAL PRIMARY KEY,
    loan_id INT REFERENCES loans(loan_id) NOT NULL,
    emi_number INT NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    paid_amount NUMERIC(15, 2) DEFAULT 0.00,
    paid_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID', 'OVERDUE'))
);
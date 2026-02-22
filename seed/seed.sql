-- Customers
INSERT INTO customers (first_name, last_name, dob, email, mobile) VALUES
('Rahul', 'Sharma', '1990-05-15', 'rahul.sharma@gmail.com', '9876543210'),
('Priya', 'Mehta', '1995-08-22', 'priya.mehta@gmail.com', '9823456710'),
('Arjun', 'Nair', '1988-11-30', 'arjun.nair@gmail.com', '9012345678'),
('Sneha', 'Reddy', '1993-03-10', 'sneha.reddy@gmail.com', '9765432109'),
('Vikram', 'Singh', '1985-07-25', 'vikram.singh@gmail.com', '9654321098');

-- Branches
INSERT INTO branches (branch_name, address, city, state, ifsc_code) VALUES
('MG Road Branch', '12 MG Road', 'Bangalore', 'Karnataka', 'BANK0001234'),
('Connaught Place', '5 CP Block A', 'Delhi', 'Delhi', 'BANK0002345'),
('Banjara Hills', '23 Road No 12', 'Hyderabad', 'Telangana', 'BANK0003456');

-- Accounts
INSERT INTO accounts (customer_id, branch_id, account_number, balance, account_type, currency) VALUES
(1, 1, 'ACC0000000001', 25000.00, 'savings', 'INR'),
(2, 2, 'ACC0000000002', 50000.00, 'current', 'INR'),
(3, 3, 'ACC0000000003', 15000.00, 'savings', 'INR'),
(4, 1, 'ACC0000000004', 75000.00, 'savings', 'INR'),
(5, 2, 'ACC0000000005', 10000.00, 'current', 'INR');

INSERT INTO transactions (account_id, tx_type, amount, balance_after, related_account, description) VALUES
-- Account 1 at 0, deposits 25k
(1, 'DEPOSIT', 25000.00, 25000.00, NULL, 'Initial account funding'),
-- Withdrawa
(3, 'WITHDRAWAL', 5000.00, 10000.00, NULL, 'ATM Cash Withdrawal - Banjara Hills'),
/*from Sneha to vikrm*/
(4, 'DEBIT', 5000.00, 70000.00, 5, 'Transfer to Vikram Singh'),
(5, 'CREDIT', 5000.00, 15000.00, 4, 'Transfer in from Sneha Reddy');

-- Employees
INSERT INTO employees (branch_id, name, email, role, status, salary, hired_at)
VALUES 
    (1, 'Alice Thompson', 'alice.t@globalbank.com', 'Manager', 'Active', 95000.00, '2020-01-15'),
    (1, 'Marcus Chen', 'm.chen@globalbank.com', 'Teller', 'Active', 48000.00, '2022-06-10'),
    (2, 'Sarah Jenkins', 's.jenkins@globalbank.com', 'Loan Officer', 'Active', 62000.00, '2021-03-22'),
    (2, 'Robert Miller', 'r.miller@globalbank.com', 'Teller', 'On Leave', 45000.00, '2023-11-01'),
    (3, 'Elena Rodriguez', 'e.rodriguez@globalbank.com', 'Auditor', 'Active', 78000.00, '2019-08-30'),
    (1, 'Kevin White', 'k.white@globalbank.com', 'IT Support', 'Active', 55000.00, '2024-02-12'),
    (3, 'Jessica Wu', 'j.wu@globalbank.com', 'Intern', 'Active', 32000.00, '2024-05-01');

INSERT INTO cards 
(account_id, card_number, card_type, expiry_date, cvv, status, credit_limit, withdrawal_limit)
VALUES
-- Rahul Sharma (account 1)
(1, '4532123412341111', 'Debit',  '2029-12-31', '123', 'Active', NULL, 20000),
(1, '4532123412341112', 'Credit', '2031-06-30', '321', 'Active', 50000, NULL),

-- Priya Mehta (account 2)
(2, '4532123412342221', 'Debit',  '2029-03-31', '234', 'Active', NULL, 18000),
(2, '4532123412342222', 'Credit', '2030-11-30', '432', 'Active', 100000, NULL),

-- Arjun Nair (account 3)
(3, '4532123412343331', 'Debit',  '2028-10-31', '345', 'Active', NULL, 15000),

-- Sneha Reddy (account 4)
(4, '4532123412344441', 'Debit',  '2029-09-30', '456', 'Active', NULL, 25000),
(4, '4532123412344442', 'Credit', '2032-02-28', '654', 'Active', 75000, NULL),

-- Vikram Singh (account 5)
(5, '4532123412345551', 'Debit',  '2029-05-31', '567', 'Active', NULL, 12000),
(5, '4532123412345552', 'Credit', '2031-08-31', '765', 'Active', 60000, NULL);

-- Fixed Deposits
INSERT INTO fixed_deposits 
(customer_id, linked_account_id, fd_number, principal_amount, interest_rate, tenure_months, start_date, maturity_date, maturity_amount, status) 
VALUES
-- Rahul Sharma (Active FD, matures later in 2026)
(1, 1, 'FD0000000001', 100000.00, 6.50, 12, '2025-08-01', '2026-08-01', 106500.00, 'ACTIVE'),

-- Priya Mehta (Active FD, long term)
(2, 2, 'FD0000000002', 500000.00, 7.00, 24, '2025-01-15', '2027-01-15', 570000.00, 'ACTIVE'),

-- Arjun Nair (Matured FD, started in 2024, matured in 2025)
(3, 3, 'FD0000000003', 50000.00, 6.00, 12, '2024-02-10', '2025-02-10', 53000.00, 'MATURED'),

-- Sneha Reddy (Prematurely Closed FD)
(4, 4, 'FD0000000004', 200000.00, 6.50, 36, '2024-05-01', '2027-05-01', 239000.00, 'PREMATURELY_CLOSED'),

-- Vikram Singh (Active FD, just opened recently)
(5, 5, 'FD0000000005', 75000.00, 5.50, 6, '2026-01-10', '2026-07-10', 77062.50, 'ACTIVE');

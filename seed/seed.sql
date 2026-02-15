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
INSERT INTO transactions (account_id, tx_type, amount, balance_after, related_account, description) VALUES
-- Account 1 at 0, deposits 25k
(1, 'DEPOSIT', 25000.00, 25000.00, NULL, 'Initial account funding'),
-- Withdrawa
(3, 'WITHDRAWAL', 5000.00, 10000.00, NULL, 'ATM Cash Withdrawal - Banjara Hills'),
/*from Sneha to vikrm*/
(4, 'DEBIT', 5000.00, 70000.00, 5, 'Transfer to Vikram Singh'),
(5, 'CREDIT', 5000.00, 15000.00, 4, 'Transfer in from Sneha Reddy');
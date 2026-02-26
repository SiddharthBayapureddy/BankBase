INSERT INTO loans 
(customer_id, branch_id, linked_account_id, loan_number, loan_type, principal_amount, interest_rate, tenure_months, emi_amount, outstanding_balance, disbursement_date, status) 
VALUES
-- 1. Rahul Sharma: Active Home Loan (Paying off normally)
(1, 1, 1, 'LN0000000011', 'Home', 5000000.00, 8.50, 240, 43391.00, 4750000.00, '2024-05-10', 'ACTIVE'),

-- 2. Priya Mehta: Active Business Loan (Shorter tenure, higher interest)
(2, 2, 2, 'LN0000000012', 'Business', 2000000.00, 10.50, 60, 42988.00, 1650000.00, '2025-01-15', 'ACTIVE'),

-- 3. Arjun Nair: Defaulted Personal Loan (Stopped paying EMIs)
(3, 3, 3, 'LN0000000013', 'Personal', 300000.00, 14.00, 36, 10254.00, 180000.00, '2024-02-01', 'DEFAULTED'),

-- 4. Sneha Reddy: Closed Education Loan (Fully paid off, balance is 0)
(4, 1, 4, 'LN0000000014', 'Education', 1500000.00, 9.50, 120, 19409.00, 0.00, '2018-08-01', 'CLOSED'),

-- 5. Vikram Singh: Pending Auto Loan (Approved but not yet disbursed)
(5, 2, 5, 'LN0000000015', 'Auto', 800000.00, 9.00, 60, 16606.00, 800000.00, NULL, 'PENDING');
-- Loan EMI Seed Data
-- Realistic EMI payment schedules for all 5 loans

-- ============================================
-- Loan 1: Rahul Sharma - Home Loan (ACTIVE)
-- Started May 2024, showing first 6 EMIs (5 paid, 1 pending)
-- ============================================
INSERT INTO loan_emi (loan_id, emi_number, due_date, amount, paid_amount, paid_at, status) VALUES
(1, 1, '2024-06-10', 43391.00, 43391.00, '2024-06-09 14:23:00', 'PAID'),
(1, 2, '2024-07-10', 43391.00, 43391.00, '2024-07-08 10:15:00', 'PAID'),
(1, 3, '2024-08-10', 43391.00, 43391.00, '2024-08-09 16:45:00', 'PAID'),
(1, 4, '2024-09-10', 43391.00, 43391.00, '2024-09-10 09:30:00', 'PAID'),
(1, 5, '2024-10-10', 43391.00, 43391.00, '2024-10-08 11:20:00', 'PAID'),
(1, 6, '2024-11-10', 43391.00, 0.00, NULL, 'PENDING');

-- ============================================
-- Loan 2: Priya Mehta - Business Loan (ACTIVE)
-- Started Jan 2025, showing first 4 EMIs (3 paid, 1 pending)
-- ============================================
INSERT INTO loan_emi (loan_id, emi_number, due_date, amount, paid_amount, paid_at, status) VALUES
(2, 1, '2025-02-15', 42988.00, 42988.00, '2025-02-14 13:45:00', 'PAID'),
(2, 2, '2025-03-15', 42988.00, 42988.00, '2025-03-14 10:30:00', 'PAID'),
(2, 3, '2025-04-15', 42988.00, 42988.00, '2025-04-13 15:20:00', 'PAID'),
(2, 4, '2025-05-15', 42988.00, 0.00, NULL, 'PENDING');

-- ============================================
-- Loan 3: Arjun Nair - Personal Loan (DEFAULTED)
-- Started Feb 2024, showing first 8 EMIs (4 paid, 4 overdue - loan defaulted)
-- ============================================
INSERT INTO loan_emi (loan_id, emi_number, due_date, amount, paid_amount, paid_at, status) VALUES
(3, 1, '2024-03-01', 10254.00, 10254.00, '2024-02-28 12:00:00', 'PAID'),
(3, 2, '2024-04-01', 10254.00, 10254.00, '2024-03-30 14:30:00', 'PAID'),
(3, 3, '2024-05-01', 10254.00, 10254.00, '2024-05-01 09:15:00', 'PAID'),
(3, 4, '2024-06-01', 10254.00, 10254.00, '2024-06-02 16:45:00', 'PAID'),
(3, 5, '2024-07-01', 10254.00, 0.00, NULL, 'OVERDUE'),
(3, 6, '2024-08-01', 10254.00, 0.00, NULL, 'OVERDUE'),
(3, 7, '2024-09-01', 10254.00, 0.00, NULL, 'OVERDUE'),
(3, 8, '2024-10-01', 10254.00, 0.00, NULL, 'OVERDUE');

-- ============================================
-- Loan 4: Sneha Reddy - Education Loan (CLOSED - Fully Paid)
-- Started Aug 2018, showing last 6 EMIs all paid (loan closed after 120 EMIs)
-- ============================================
INSERT INTO loan_emi (loan_id, emi_number, due_date, amount, paid_amount, paid_at, status) VALUES
(4, 115, '2028-02-01', 19409.00, 19409.00, '2028-01-30 11:20:00', 'PAID'),
(4, 116, '2028-03-01', 19409.00, 19409.00, '2028-02-28 14:35:00', 'PAID'),
(4, 117, '2028-04-01', 19409.00, 19409.00, '2028-03-30 09:45:00', 'PAID'),
(4, 118, '2028-05-01', 19409.00, 19409.00, '2028-04-29 13:10:00', 'PAID'),
(4, 119, '2028-06-01', 19409.00, 19409.00, '2028-05-31 10:25:00', 'PAID'),
(4, 120, '2028-07-01', 19409.00, 19409.00, '2028-07-01 15:50:00', 'PAID');

-- ============================================
-- Loan 5: Vikram Singh - Auto Loan (PENDING - Not Yet Disbursed)
-- No EMIs created yet since loan is still pending approval/disbursement
-- ============================================
-- (No entries - loan not yet active)
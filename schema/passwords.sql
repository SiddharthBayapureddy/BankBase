ALTER TABLE customers 
ADD COLUMN password_hash VARCHAR(255);

ALTER TABLE employees 
ADD COLUMN password_hash VARCHAR(255);
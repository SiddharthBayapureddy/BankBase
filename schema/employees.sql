CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    branch_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'Active' CHECK (
        status IN ('Active', 'On Leave', 'Terminated', 'Suspended')
    ),
    salary NUMERIC(15, 2) NOT NULL CHECK (salary > 0), 
    hired_at DATE DEFAULT CURRENT_DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_branch 
        FOREIGN KEY (branch_id) 
        REFERENCES branches (branch_id) 
        ON DELETE CASCADE
);

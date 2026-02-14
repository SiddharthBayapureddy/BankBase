CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(30),
    address VARCHAR(150),
    city VARCHAR(50),
    state VARCHAR(50),
    ifsc_code VARCHAR(11) UNIQUE
);

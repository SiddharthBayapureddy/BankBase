CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    dob DATE,
    email VARCHAR(255),
    mobile VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Connect to the default database (e.g., postgres)
\c postgres;

-- Create a new database (you can change the name as needed)
CREATE DATABASE temp_db;

-- Connect to the newly created database
\c temp_db;

-- Create sample tables

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL
);

-- Order items table (associating products with orders)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Insert sample data into the tables

-- Insert into users
INSERT INTO users (first_name, last_name, email)
VALUES 
    ('John', 'Doe', 'john.doe@example.com'),
    ('Jane', 'Smith', 'jane.smith@example.com');

-- Insert into products
INSERT INTO products (product_name, price, stock_quantity)
VALUES 
    ('Laptop', 999.99, 50),
    ('Headphones', 49.99, 200),
    ('Keyboard', 69.99, 150);

-- Insert an order for John
INSERT INTO orders (user_id, total_amount)
VALUES (1, 1049.98);

-- Insert order items for John's order (Laptop and Headphones)
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES
    (1, 1, 1, 999.99),  -- Laptop
    (1, 2, 1, 49.99);   -- Headphones

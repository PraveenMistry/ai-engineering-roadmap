-- Day 15 — Schema (SQLite dialect)
--
-- Portable to PostgreSQL with two changes, noted where they occur:
--   1. INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL PRIMARY KEY
--   2. TEXT for dates -> DATE / TIMESTAMP
-- Everything else (column names, relationships, constraints) is
-- standard SQL and needs no changes.

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Postgres: SERIAL PRIMARY KEY
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    invoice_date TEXT NOT NULL,  -- Postgres: DATE
    status TEXT NOT NULL CHECK (status IN ('paid', 'unpaid'))
);

CREATE TABLE invoice_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL  -- captured at time of sale, may differ from products.unit_price later
);

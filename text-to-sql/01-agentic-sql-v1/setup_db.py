"""
Day 15 — Database setup

Builds company.db from schema.sql and inserts fixed seed data, with
invoice dates computed RELATIVE TO TODAY rather than hardcoded calendar
dates. This means "revenue last month" always refers to a real month
relative to whenever you run this, instead of going stale.

The actual amounts, quantities, and row counts are fixed and documented
in README.md / evaluation/test_cases.json, so expected answers stay
correct regardless of when this runs — only the calendar labels shift.
"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "company.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema", "schema.sql")


def month_offset_date(offset_months: int, day: int = 10) -> str:
    """Returns an ISO date string `day` days into the month that is
    `offset_months` months before/after the current month."""
    today = date.today()
    month = today.month - 1 + offset_months  # zero-indexed
    year = today.year + month // 12
    month = month % 12 + 1
    return date(year, month, day).isoformat()


CUSTOMERS = [
    ("Acme Corp", "billing@acme.example"),
    ("Globex Inc", "billing@globex.example"),
    ("Initech", "billing@initech.example"),
    ("Umbrella Corp", "billing@umbrella.example"),
    ("Stark Industries", "billing@stark.example"),
    ("Wayne Enterprises", "billing@wayne.example"),
    ("Wonka Industries", "billing@wonka.example"),
    ("Hooli", "billing@hooli.example"),
]

PRODUCTS = [
    ("Widget A", 50.0),
    ("Widget B", 75.0),
    ("Gadget X", 120.0),
    ("Gadget Y", 200.0),
    ("Service Plan", 500.0),
]

# (customer_index[1-based], month_offset, status, [(product_index[1-based], quantity), ...])
INVOICES = [
    (1, -2, "paid",   [(1, 2)]),                 # 100
    (2, -2, "paid",   [(2, 1), (3, 1)]),          # 195
    (3, -2, "unpaid", [(1, 1)]),                  # 50
    (4, -2, "paid",   [(4, 1)]),                  # 200
    (5, -2, "paid",   [(5, 1)]),                  # 500

    (1, -1, "paid",   [(2, 2)]),                  # 150
    (2, -1, "unpaid", [(3, 1)]),                  # 120
    (6, -1, "paid",   [(1, 3)]),                  # 150
    (7, -1, "paid",   [(5, 1)]),                  # 500
    (8, -1, "paid",   [(4, 2)]),                  # 400

    (1, 0, "paid",    [(1, 1)]),                  # 50
    (3, 0, "unpaid",  [(2, 1)]),                  # 75
    (5, 0, "paid",    [(3, 2)]),                  # 240
    (6, 0, "paid",    [(4, 1)]),                  # 200
    (7, 0, "paid",    [(5, 1)]),                  # 500
]


def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    cursor.executemany(
        "INSERT INTO customers (name, email) VALUES (?, ?)", CUSTOMERS
    )
    cursor.executemany(
        "INSERT INTO products (name, unit_price) VALUES (?, ?)", PRODUCTS
    )

    for customer_idx, month_offset, status, items in INVOICES:
        invoice_date = month_offset_date(month_offset)
        cursor.execute(
            "INSERT INTO invoices (customer_id, invoice_date, status) VALUES (?, ?, ?)",
            (customer_idx, invoice_date, status),
        )
        invoice_id = cursor.lastrowid
        for product_idx, quantity in items:
            unit_price = PRODUCTS[product_idx - 1][1]
            cursor.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) "
                "VALUES (?, ?, ?, ?)",
                (invoice_id, product_idx, quantity, unit_price),
            )

    conn.commit()
    conn.close()
    print(f"Database built at {DB_PATH}")
    print(f"  {len(CUSTOMERS)} customers, {len(PRODUCTS)} products, {len(INVOICES)} invoices")


if __name__ == "__main__":
    build_database()

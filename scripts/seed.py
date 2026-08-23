import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "report.db"


PRODUCTS = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "USB-C Hub",
    "Laptop Stand",
    "Webcam",
    "Bluetooth Headphones",
]


def create_database(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at DATE NOT NULL
        )
        """
    )


def seed_orders(connection, count=200):
    # Make the seed script safe to run repeatedly.
    connection.execute("DELETE FROM orders")

    today = date.today()

    customers = [
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Emma",
        "Frank",
        "Grace",
        "Henry",
        "Ivy",
        "Jack",
    ]

    orders = []

    for _ in range(count):
        customer = random.choice(customers)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5, 200), 2)

        days_ago = random.randint(0, 29)
        created_at = today - timedelta(days=days_ago)

        orders.append(
            (customer, product, amount, created_at.isoformat())
        )

    connection.executemany(
        """
        INSERT INTO orders (customer, product, amount, created_at)
        VALUES (?, ?, ?, ?)
        """,
        orders,
    )


def main():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        create_database(connection)
        seed_orders(connection)
        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        print(f"Seed complete: {count} orders inserted.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
"""Database setup for the boba tea agent.

This module creates the SQLite database and populates the product tables
based on the schema defined in app.schema.
"""

import sqlite3
from pathlib import Path

from app.schema import Size

DATABASE_PATH = Path(__file__).parent.parent / "boba_tea.db"

PRODUCTS = [
    {
        "product_id": 1,
        "name": "Taro Milk Tea",
        "category": "Milk Tea",
        "description": "Creamy milk tea blended with taro root for a nutty, sweet flavor.",
    },
    {
        "product_id": 2,
        "name": "Brown Sugar Boba",
        "category": "Milk Tea",
        "description": "Rich milk tea with brown sugar syrup and chewy tapioca pearls.",
    },
    {
        "product_id": 3,
        "name": "Mango Green Tea",
        "category": "Fruit Tea",
        "description": "Refreshing green tea infused with sweet mango flavor.",
    },
]

PRODUCT_PRICE_SIZES = [
    {"product_id": 1, "price": 4.50, "size": Size.SMALL.value},
    {"product_id": 1, "price": 5.50, "size": Size.MEDIUM.value},
    {"product_id": 1, "price": 6.50, "size": Size.LARGE.value},
    {"product_id": 2, "price": 6.00, "size": Size.SMALL.value},
    {"product_id": 2, "price": 7.00, "size": Size.MEDIUM.value},
    {"product_id": 2, "price": 8.00, "size": Size.LARGE.value},
    {"product_id": 3, "price": 5.00, "size": Size.SMALL.value},
    {"product_id": 3, "price": 6.00, "size": Size.MEDIUM.value},
    {"product_id": 3, "price": 7.00, "size": Size.LARGE.value},
]


def create_tables(conn: sqlite3.Connection) -> None:
    """Create Product, ProductPriceSize, OrderResponse, and OrderDetails tables.

    Args:
        conn (sqlite3.Connection): An active SQLite connection.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Product (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ProductPriceSize (
            ProductPriceSize_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            size TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES Product(product_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS OrderResponse (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            total_price REAL NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS OrderDetails (
            order_details_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES OrderResponse(order_id),
            FOREIGN KEY (product_id) REFERENCES Product(product_id)
        )
        """
    )

    conn.commit()


def seed_data(conn: sqlite3.Connection) -> None:
    """Insert seed products and prices into the database.

    Args:
        conn (sqlite3.Connection): An active SQLite connection.
    """
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT OR REPLACE INTO Product (product_id, name, category, description)
        VALUES (:product_id, :name, :category, :description)
        """,
        PRODUCTS,
    )

    cursor.execute("DELETE FROM ProductPriceSize")
    cursor.executemany(
        """
        INSERT INTO ProductPriceSize (product_id, price, size)
        VALUES (:product_id, :price, :size)
        """,
        PRODUCT_PRICE_SIZES,
    )

    conn.commit()


def init_database(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Initialize the database: create tables and seed data.

    Args:
        db_path (Path | str | None): Optional path to the SQLite database file.
            Defaults to the project-root ``boba_tea.db``.

    Returns:
        sqlite3.Connection: An open connection to the initialized database.
    """
    path = Path(db_path) if db_path else DATABASE_PATH
    conn = sqlite3.connect(path)
    return conn

def create_tables_n_seed_data(conn: sqlite3.Connection) -> None:
    """Create tables and seed data in the database.

    Args:
        conn (sqlite3.Connection): An active SQLite connection.
    """
    create_tables(conn)
    seed_data(conn)


if __name__ == "__main__":
    with init_database() as connection:
        create_tables_n_seed_data(connection)
        print(f"Database initialized at: {DATABASE_PATH}")

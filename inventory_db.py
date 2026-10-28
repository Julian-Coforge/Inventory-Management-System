import sqlite3
from pathlib import Path


def connect(path: str):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def create_schema(conn):
    sql = (Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(sql)

def seed(conn):
    suppliers = [
        (1, "Tools Inc", "555-0101", "contact@toolsinc.com"),
        (2, "MadeInChina", "555-0102", "sales@madeinchina.com"),
    ]

    products = [
        (1, "TOOL-Hammer", "Hammer", "Tool", 1, 1500, 25, 5),
        (2, "MAT-WoodPlank", "Wooden Plank", "Material", 2, 800, 100, 20),
        (3, "MAT-SteelSheet", "Steel Sheet", "Material", 2, 2500, 5, 10),
        (4, "TOOL-PhillipsScrewdriver", "Phillips Head Screwdriver",
         "Tool", 1, 1200, 30, 5),
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO Suppliers
        (SupplierID, Name, Phone, Email)
        VALUES (?, ?, ?, ?)
    """, suppliers)

    conn.executemany("""
        INSERT OR IGNORE INTO Products
        (ProductID, SKU, Name, Category, SupplierID,
         UnitPrice, CurrentStock, ReorderLevel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    conn.commit()

def add_product(conn, sku: str, name: str, category: str, supplier_id: int, unit_price: int, current_stock: int, reorder_level: int):
    product_tuple = (sku, name, category, supplier_id, unit_price, current_stock, reorder_level)
    cursor = conn.execute(
        """INSERT INTO Products (SKU, Name, 
        Category, SupplierID, UnitPrice, CurrentStock, 
        ReorderLevel) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        product_tuple
    )
    conn.commit()
    return cursor.lastrowid

def get_product(conn, sku: str):
    product = conn.execute(
        """SELECT * FROM Products WHERE SKU = ?""",
        (sku,)
    ).fetchone()
    return product

def change_price(conn, sku: str, new_price: int):
    price_tuple = (new_price, sku)
    conn.execute(
        """UPDATE Products SET UnitPrice = ? WHERE SKU = ?""",
        price_tuple
    )
    conn.commit()

def delete_product(conn, sku: str):
    conn.execute(
        """DELETE FROM Products WHERE SKU = ?""",
        (sku,)
    )
    conn.commit()
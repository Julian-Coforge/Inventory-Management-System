import sqlite3

import pytest

from inventory_db import connect, create_schema
from seed_db import seed


def test_foreign_keys_are_on():
    conn = connect(":memory:")
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1

def test_table_exists():
    conn = connect(":memory:")
    create_schema(conn)
    row = conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",("Products",),).fetchone()
    assert row is not None

def test_refuse_wrong_data():
    conn = connect(":memory:")
    create_schema(conn)
    conn.execute("INSERT INTO Suppliers (SupplierID, Name) VALUES (?, ?)", (1, "Julian"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO Suppliers (Phone) VALUES (?)", ("Julian",))

def test_negative_stock_rejected():
    conn = connect(":memory:")
    create_schema(conn)
    conn.execute("INSERT INTO Suppliers (SupplierID, Name) VALUES (?, ?)", (1, "Julian"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO Products (ProductID, SKU, Name, Category, SupplierID, UnitPrice, CurrentStock, ReorderLevel) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (1, "TOOL", "Hammer", "Tools", 1, 1000, -1, 5))

def test_invalid_reason():
    conn = connect(":memory:")
    create_schema(conn)
    conn.execute("INSERT INTO Suppliers (SupplierID, Name) VALUES (?, ?)", (1, "Julian"))
    conn.execute("INSERT INTO Products (ProductID, SKU, Name, Category, SupplierID, UnitPrice, CurrentStock, ReorderLevel) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (1, "TOOL", "Hammer", "Tools", 1, 1000, 5, 5))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO StockMovements (MovementID, ProductID, Change, Reason, WhenHappened) VALUES (?, ?, ?, ?, ?)", (1, 1, 50, 'test', "Today"))

def test_no_foreign_key():
    conn = connect(":memory:")
    create_schema(conn)
    conn.execute("INSERT INTO Suppliers (SupplierID, Name) VALUES (?, ?)", (1, "Julian"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO Products (ProductID, SKU, Name, Category, SupplierID, UnitPrice, CurrentStock, ReorderLevel) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (1, "TOOL", "Hammer", "Tools", 2, 1000, 1, 5))

def test_seed():
    conn = connect(":memory:")
    create_schema(conn)
    seed(conn)
    row_product = conn.execute("SELECT COUNT(*) FROM Products").fetchone()
    row_supplier = conn.execute("SELECT COUNT(*) FROM Suppliers").fetchone()
    assert row_product[0] == 12
    assert row_supplier[0] == 4


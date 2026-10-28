import sqlite3

import pytest

from inventory_db import connect, create_schema, seed, add_product, get_product


def test_add_product(inventory_database):
    new_id = add_product(inventory_database, "TOOL-Powerdrill", "Powerdrill", "Tool", 2, 4999, 15, 10)
    row = inventory_database.execute(
        "SELECT ProductID, Name FROM Products WHERE ProductID = ?", (new_id,)
    ).fetchone()
    assert row["Name"] == "Powerdrill"
    assert row["UnitPrice"] == 4999

def test_get_product(inventory_database):
    product = get_product(inventory_database, "TOOL-Hammer")
    assert product["Name"] == "Hammer"

def test_get_missing_product(inventory_database):
    assert get_product(inventory_database, "TOOL-Powerdrill") is None
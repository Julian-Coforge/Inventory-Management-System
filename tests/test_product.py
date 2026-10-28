import sqlite3

import pytest

from inventory_db import add_product, get_product, change_price, delete_product, search_products


def test_add_product(inventory_database):
    new_id = add_product(inventory_database, "TOOL-Powerdrill", "Powerdrill", "Tool", 2, 4999, 15, 10)
    row = inventory_database.execute(
        "SELECT Name, UnitPrice FROM Products WHERE ProductID = ?", (new_id,)
    ).fetchone()
    assert row["Name"] == "Powerdrill"
    assert row["UnitPrice"] == 4999

def test_get_product(inventory_database):
    product = get_product(inventory_database, "TOOL-Hammer")
    assert product["Name"] == "Hammer"

def test_get_missing_product(inventory_database):
    assert get_product(inventory_database, "TOOL-Powerdrill") is None

def test_change_product_price(inventory_database):
    change_price(inventory_database, "TOOL-Hammer", 2000)
    row = get_product(inventory_database, "TOOL-Hammer")
    assert row["UnitPrice"] == 2000

def test_delete_product(inventory_database):
    delete_product(inventory_database, "TOOL-Hammer")
    assert get_product(inventory_database, "TOOL-Hammer") is None

def test_search_product_category(inventory_database):
    results = search_products(inventory_database, category="Tool")
    names = {row["Name"] for row in results}
    assert names == {"Phillips Head Screwdriver", "Hammer"}

def test_search_products_no_filters(inventory_database):
    results = search_products(inventory_database)
    assert len(results) == 4

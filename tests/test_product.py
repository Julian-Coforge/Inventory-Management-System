import sqlite3

import pytest

from inventory_db import (
    DuplicateSKUError,
    NegativePriceError,
    NegativeQuantityError,
    ProductHasSalesError,
    UnknownSupplierError,
    add_product,
    change_price,
    delete_product,
    get_product,
    record_sale,
    search_products,
)


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

def test_duplicate_SKU_rejected(inventory_database):
    with pytest.raises(DuplicateSKUError):
        add_product(inventory_database, "TOOL-Hammer", "Hammer", "Tool", 2, 4999, 15, 10)

def test_negative_price_rejected(inventory_database):
    with pytest.raises(NegativePriceError):
        add_product(inventory_database, "TOOL-Powerdrill", "Powerdrill", "Tool", 2, -4999, 15, 10)

def test_unknown_supplier(inventory_database):
    with pytest.raises(UnknownSupplierError):
        add_product(inventory_database, "TOOL-Powerdrill", "Powerdrill", "Tool", 99, 4999, 15, 10)

def test_negative_quantity_rejected(inventory_database):
    with pytest.raises(NegativeQuantityError):
        add_product(inventory_database, "TOOL-Powerdrill", "Powerdrill", "Tool", 2, 4999, -1, 10)

def test_good_path(inventory_database):
    before = get_product(inventory_database, "TOOL-Hammer")
    sale_id = record_sale(inventory_database, [("TOOL-Hammer", 2)])
    after = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    assert after == before["CurrentStock"] - 2
    assert sale_id

def test_sale_writes_rows(inventory_database):
    sale_id = record_sale(inventory_database, [("TOOL-Hammer", 2)])
    product = get_product(inventory_database, "TOOL-Hammer")

    item = inventory_database.execute(
        "SELECT Quantity FROM SaleItems WHERE SaleID = ?", (sale_id,)
    ).fetchone()
    assert item["Quantity"] == 2

    log = inventory_database.execute(
        "SELECT Change, Reason FROM StockMovements WHERE ProductID = ? AND Reason = 'sale'",
        (product["ProductID"],),
    ).fetchone()
    assert log["Change"] == -2
    assert log["Reason"] == "sale"

def test_failed_sale_saves_nothing(inventory_database):
    quantity_before = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    sales_before = inventory_database.execute("SELECT COUNT(*) FROM Sales").fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError):
        record_sale(inventory_database, [("TOOL-Hammer", quantity_before + 1)])

    quantity_after = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    sales_after = inventory_database.execute("SELECT COUNT(*) FROM Sales").fetchone()[0]
    assert quantity_after == quantity_before
    assert sales_after == sales_before

def test_delete_product_with_sale_rejected(inventory_database):
    record_sale(inventory_database, [("TOOL-Hammer", 1)])
    with pytest.raises(ProductHasSalesError):
        delete_product(inventory_database, "TOOL-Hammer")
    assert get_product(inventory_database, "TOOL-Hammer") is not None

def test_get_product_includes_author_name(inventory_database):
    product = get_product(inventory_database, "TOOL-Hammer")
    assert product["SupplierID"] == 1

def test_negative_price_on_update_rejected(inventory_database):
    with pytest.raises(NegativePriceError):
        change_price(inventory_database, "TOOL-Hammer", -1)

def test_search_supplier_name(inventory_database):
    results = search_products(inventory_database, text="China")
    names = {row["Name"] for row in results}
    assert names == {"Wooden Plank", "Steel Sheet"}

def test_search_product_name(inventory_database):
    results = search_products(inventory_database, text="Ham")
    names = {row["Name"] for row in results}
    assert names == {"Hammer"}

def test_search_supplier_name(inventory_database):
    results = search_products(inventory_database, text="TOOL")
    names = {row["Name"] for row in results}
    assert names == {"Phillips Head Screwdriver", "Hammer"}
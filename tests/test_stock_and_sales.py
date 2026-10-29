import pytest

from inventory_db import (
    AdjustBelowZeroError,
    DuplicateSaleLineError,
    NegativeQuantityError,
    UnknownSKUError,
    adjust,
    get_product,
    record_sale,
    restock,
)


def test_restock_increases_stock_and_records_movement(inventory_database):
    before = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    restock(inventory_database, "TOOL-Hammer", 10, when="2026-01-01T10:00:00")
    after = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    movement = inventory_database.execute(
        "SELECT * FROM StockMovements ORDER BY MovementID DESC LIMIT 1"
    ).fetchone()
    assert after == before + 10
    assert movement["Change"] == 10
    assert movement["Reason"] == "restock"
    assert movement["WhenHappened"] == "2026-01-01T10:00:00"

def test_restock_zero_rejected(inventory_database):
    before = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    with pytest.raises(NegativeQuantityError):
        restock(inventory_database, "TOOL-Hammer", 0)
    assert get_product(inventory_database, "TOOL-Hammer")["CurrentStock"] == before

def test_adjust_decreases_stock_and_records_movement(inventory_database):
    before = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    adjust(inventory_database, "TOOL-Hammer", -3, when="2026-01-01T10:00:00")
    after = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    movement = inventory_database.execute(
        "SELECT * FROM StockMovements ORDER BY MovementID DESC LIMIT 1"
    ).fetchone()
    assert after == before - 3
    assert movement["Change"] == -3
    assert movement["Reason"] == "adjustment"

def test_adjust_below_zero_rejected(inventory_database):
    before = get_product(inventory_database, "TOOL-Hammer")["CurrentStock"]
    count_before = inventory_database.execute(
        "SELECT COUNT(*) FROM StockMovements"
    ).fetchone()[0]
    with pytest.raises(AdjustBelowZeroError):
        adjust(inventory_database, "TOOL-Hammer", -100)
    assert get_product(inventory_database, "TOOL-Hammer")["CurrentStock"] == before
    count_after = inventory_database.execute(
        "SELECT COUNT(*) FROM StockMovements"
    ).fetchone()[0]
    assert count_after == count_before

def test_record_sale_uses_fixed_time(inventory_database):
    record_sale(inventory_database, [("TOOL-Hammer", 1)], when="2026-01-01T10:00:00")
    sale = inventory_database.execute(
        "SELECT SaleDateTime FROM Sales ORDER BY SaleID DESC LIMIT 1"
    ).fetchone()
    assert sale["SaleDateTime"] == "2026-01-01T10:00:00"

def test_duplicate_sku_in_sale_rejected(inventory_database):
    count_before = inventory_database.execute(
        "SELECT COUNT(*) FROM Sales"
    ).fetchone()[0]
    with pytest.raises(DuplicateSaleLineError):
        record_sale(inventory_database, [("TOOL-Hammer", 1), ("TOOL-Hammer", 2)])
    count_after = inventory_database.execute(
        "SELECT COUNT(*) FROM Sales"
    ).fetchone()[0]
    assert count_after == count_before

def test_unknown_sku_in_sale_rolls_back(inventory_database):
    count_before = inventory_database.execute(
        "SELECT COUNT(*) FROM Sales"
    ).fetchone()[0]
    with pytest.raises(UnknownSKUError):
        record_sale(inventory_database, [("TOOL-Hammer", 1), ("UNKNOWN-SKU", 1)])
    count_after = inventory_database.execute(
        "SELECT COUNT(*) FROM Sales"
    ).fetchone()[0]
    assert count_after == count_before

from inventory_db import (
    low_stock_report,
    never_sold_report,
    record_sale,
    sales_by_product_report,
    stock_value_by_supplier_report,
)


def test_stock_value_by_supplier_report(inventory_database):
    results = stock_value_by_supplier_report(inventory_database)
    assert results[0]["SupplierName"] == "MadeInChina"
    assert results[0]["StockValue"] == 164500
    assert results[1]["SupplierName"] == "Tools Inc"
    assert results[1]["StockValue"] == 151500
    assert results[2]["SupplierName"] == "PaintPro"
    assert results[2]["StockValue"] == 70200
    assert results[3]["SupplierName"] == "BuildRight Supplies"
    assert results[3]["StockValue"] == 18100

def test_low_stock_report(inventory_database):
    results = low_stock_report(inventory_database)
    assert len(results) == 4
    assert results[0]["ProductSKU"] == "FAST-Bolts"
    assert results[0]["UnitsShort"] == 6
    assert results[1]["ProductSKU"] == "MAT-SteelSheet"
    assert results[1]["UnitsShort"] == 5

def test_sales_by_product_report(inventory_database):
    results = sales_by_product_report(inventory_database)
    assert results[0]["Name"] == "Wooden Plank"
    assert results[0]["UnitsSold"] == 10
    assert results[0]["Revenue"] == 8000
    assert results[1]["Name"] == "Plywood Sheet"
    assert results[1]["UnitsSold"] == 4
    assert results[1]["Revenue"] == 7200

def test_never_sold_report(inventory_database):
    record_sale(inventory_database, [("PAINT-Primer", 1)])
    results = never_sold_report(inventory_database)
    skus = {row["ProductSKU"] for row in results}
    assert len(results) == 1
    assert "PAINT-Primer" not in skus

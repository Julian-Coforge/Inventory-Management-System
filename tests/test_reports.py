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
    assert results[0]["StockValue"] == 92500
    assert results[1]["SupplierName"] == "Tools Inc"
    assert results[1]["StockValue"] == 73500

def test_low_stock_report(inventory_database):
    results = low_stock_report(inventory_database)
    assert len(results) == 1
    assert results[0]["ProductSKU"] == "MAT-SteelSheet"
    assert results[0]["UnitsShort"] == 5

def test_sales_by_product_report(inventory_database):
    record_sale(inventory_database, [("TOOL-Hammer", 2), ("MAT-SteelSheet", 1)])
    results = sales_by_product_report(inventory_database)
    assert results[0]["Name"] == "Hammer"
    assert results[0]["UnitsSold"] == 2
    assert results[0]["Revenue"] == 3000
    assert results[1]["Name"] == "Steel Sheet"
    assert results[1]["Revenue"] == 2500

def test_never_sold_report(inventory_database):
    record_sale(inventory_database, [("TOOL-Hammer", 1)])
    results = never_sold_report(inventory_database)
    skus = {row["ProductSKU"] for row in results}
    assert len(results) == 3
    assert "TOOL-Hammer" not in skus

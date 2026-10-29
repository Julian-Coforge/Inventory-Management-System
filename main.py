import os
from pathlib import Path
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
    connect,
    create_schema,
    seed,
    low_stock_report,
    never_sold_report,
    sales_by_product_report,
    stock_value_by_supplier_report
)


DEFAULT_DB = Path(__file__).parent / "inventory.db"

def get_db_path():
    return os.environ.get("INVENTORY_DB", str(DEFAULT_DB))

def main():

    print("\nWelcome the the Inventory Management System!\n")
    print("\nConnecting to Database...")
    path = get_db_path()
    connection = connect(path)
    print("\nDatabase connected! Path:" + path)
    print("\n\nCreating and seeding Database...")
    create_schema(connection)
    seed(connection)
    print("\n\nThe database is ready!")
    print("\n=====================================================\n")
    
    while True:
        option = input(
            "\nInventory Management System\n"
            "1. Search products\n"
            "2. Look up a product\n"
            "3. Add a product\n"
            "4. Restock\n"
            "5. Record a sale\n"
            "6. Report: stock value by supplier\n"
            "7. Report: low stock\n"
            "8. Report: sales by product\n"
            "9. Report: never sold\n"
            "10. Back up the database\n"
            "0. Quit\n"
            "Choose an option: "
        )


if __name__ == "__main__": 
    main()
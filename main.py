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
    stock_value_by_supplier_report,
    restock,
    adjust
)


DEFAULT_DB = Path(__file__).parent / "inventory.db"

def get_db_path():
    return os.environ.get("INVENTORY_DB", str(DEFAULT_DB))

def ask_optional_int(prompt: str):
    while True:
        output = input(prompt).strip()
        if output == '':
            return None
        try:
            result = int(output)
            return result
        except ValueError:
            print("\nPlease enter a whole number, or press Enter to skip")

def ask_int(prompt: str):
    while True:
        output = input(prompt).strip()
        if output == '':
            print("\nPlease enter a non null value")
            pass
        try:
            result = int(output)
            return result
        except ValueError:
            print("\nPlease enter a whole number, or press Enter to skip")

def menu_search(conn):

    text = input("Search text (press Enter to skip): ").strip()
    category = input("Category (press Enter to skip): ").strip()
    max_price = ask_optional_int("Max price (press Enter to skip): ")
    low_stock = input("Low stock? (True/False, press Enter to skip): ").strip()
    in_stock = input("In stock? (True/False, press Enter to skip): ").strip()

    text = text if text else None
    category = category if category else None
    low_stock = low_stock.lower() == "true" if low_stock else False
    in_stock = in_stock.lower() == "true" if in_stock else False

    results = search_products(
        conn,
        text=text,
        category=category,
        max_price=max_price,
        low_stock=low_stock,
        in_stock=in_stock
    )

    if not results:
        print("No matches.")
    for row in results:
        print(f"\n RESULT FOUND: {row['SKU']} {row['Name']} £{row['UnitPrice'] / 100:.2f} {row['CurrentStock']}")

def menu_lookup(conn):
    sku = input("Enter product SKU: ").strip
    result = get_product(conn, sku)
    if result is None:
        print("\nNo product with that SKU")
        return
    
    print("\nRESULT FOUND:")
    print(f"SKU: {result['SKU']}")
    print(f"Name: {result['Name']}")
    print(f"Category: {result['Category']}")
    print(f"Supplier: {result['SupplierName']}")
    print(f"Unit Price: £{result['UnitPrice'] / 100:.2f}")
    print(f"Current Stock: {result['CurrentStock']}")
    print(f"Reorder Level: {result['ReorderLevel']}")

def menu_add(conn):

    sku = input("Enter product SKU: ").strip()
    name = input("Enter product name: ").strip()
    category = input("Enter product category: ").strip()
    supplier_id = ask_int("Enter supplier ID: ")
    unit_price = ask_int("Enter unit price in pence: ")
    current_stock = ask_int("Enter current stock: ")
    reorder_level = ask_int("Enter reorder level: ")

    new_id = add_product(
        conn,
        sku,
        name,
        category,
        supplier_id,
        unit_price,
        current_stock,
        reorder_level
    )

    print(f"Added {name} (ID {new_id})")

def menu_restock(conn):

    sku = input("Enter product SKU: ").strip()
    amount = ask_int("Enter an amount of stock to add: ")
    restock(conn, sku, amount)
    new_product = get_product(conn, sku)
    print(f"\n RESTOCK: {new_product['SKU']} {new_product['Name']} with Stock: {new_product['CurrentStock']}")

def menu_sale(conn):
    items = []
    while True:
        sku = input("Enter product SKU: ").strip()
        if sku is None:
            break
        quantity = ask_int("Enter quantity: ")

def main():

    print("\nWelcome the the Inventory Management System!\n")
    print("\nConnecting to Database...")
    path = get_db_path()
    conn = connect(path)
    print("\nDatabase connected! Path:" + path)
    print("\n\nCreating and seeding Database...")
    create_schema(conn)
    seed(conn)
    print("\n\nThe database is ready!")
    print("\n=====================================================\n")
    
    while True:
        print("\n\n")
        option = input(
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
            "Choose an option (please enter the corresponding number): "
        ).strip()
        
        if option == "1":
            menu_search(conn)
        elif option == "2":
            menu_lookup(conn)
        elif option == "3":
            menu_add(conn)
        elif option == "4":
            menu_restock(conn)
        elif option == "5":
            menu_sale(conn)
        elif option == "6":
            print("Report: stock value by supplier")
        elif option == "7":
            print("Report: low stock")
        elif option == "8":
            print("Report: sales by product")
        elif option == "9":
            print("Report: never sold")
        elif option == "10":
            print("Back up the database")
        elif option == "0":
            print("Goodbye!")
        else:
            print("Invalid option. Please try again.")



if __name__ == "__main__": 
    main()
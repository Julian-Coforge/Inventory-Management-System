import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from inventory_db import (
    ProductError,
    add_product,
    backup,
    connect,
    create_schema,
    get_db_path,
    get_product,
    low_stock_report,
    never_sold_report,
    record_sale,
    restock,
    sales_by_product_report,
    search_products,
    stock_value_by_supplier_report,
)
from seed_db import seed


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
            continue
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
        print(f"\n RESULT FOUND: {row['SKU']} {row['Name']} ${row['UnitPrice'] / 100:.2f} {row['CurrentStock']}")

def menu_lookup(conn):
    sku = input("Enter product SKU: ").strip()
    result = get_product(conn, sku)
    if result is None:
        print("\nNo product with that SKU")
        return
    
    print("\nRESULT FOUND:")
    print(f"SKU: {result['SKU']}")
    print(f"Name: {result['Name']}")
    print(f"Category: {result['Category']}")
    print(f"Supplier: {result['SupplierName']}")
    print(f"Unit Price: ${result['UnitPrice'] / 100:.2f}")
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
        sku = input("Enter product SKU (or Enter to finish): ").strip()
        if not sku:
            break
        quantity = ask_int("Enter quantity: ")
        items.append((sku, quantity))
    sale_id = record_sale(conn, items)
    print(f"Sale {sale_id} recorded ({len(items)} lines)")

def menu_stock_value_report(conn):
    rows = stock_value_by_supplier_report(conn)
    if not rows:
        print("No products in stock")
        return
    print(f"{'Supplier':<20}{'Value':>11}")
    for row in rows:
        print(f"{row['SupplierName']:<20}${row['StockValue'] / 100:>10.2f}")

def menu_low_stock(conn):
    rows = low_stock_report(conn)
    if not rows:
        print("All products are above their reorder level")
        return
    print(f"{'SKU':<28}{'Name':<28}{'Stock':>7}{'Reorder':>9}{'Short':>7}")
    for row in rows:
        print(f"{row['ProductSKU']:<28}{row['Name']:<28}{row['CurrentStock']:>7}{row['ReorderLevel']:>9}{row['UnitsShort']:>7}")

def menu_sale_by_product(conn):
    rows = sales_by_product_report(conn)
    if not rows:
        print("There are no sales")
        return
    print(f"{'SKU':<28}{'Name':<28}{'Units':>7}{'Revenue':>11}")
    for row in rows:
        print(f"{row['ProductSKU']:<28}{row['Name']:<28}{row['UnitsSold']:>7}${row['Revenue'] / 100:>10.2f}")

def menu_never_sold(conn):
    rows = never_sold_report(conn)
    if not rows:
        print("Everything has had a sale")
        return
    print(f"{'SKU':<28}{'Name':<28}")
    for row in rows:
        print(f"{row['ProductSKU']:<28}{row['Name']:<28}")

def menu_backup(conn):
    filename = f"backup-{datetime.now():%Y%m%d-%H%M%S}.db"
    backup_path = Path(get_db_path()).parent / filename
    backup(conn, backup_path)
    print(f"\nBackup saved to {backup_path}\n")

def main():

    print("\nWelcome the the Inventory Management System!\n")
    print("\nConnecting to Database...")
    path = get_db_path()
    with closing(connect(path)) as conn:
        print("\nDatabase connected! Path:" + path)
        print("\n\nCreating and seeding Database...")
        create_schema(conn)
        seed(conn)
        print("\n\nThe database is ready!")
        print("\n=====================================================\n")

        try:
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

                try:
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
                        menu_stock_value_report(conn)
                    elif option == "7":
                        menu_low_stock(conn)
                    elif option == "8":
                        menu_sale_by_product(conn)
                    elif option == "9":
                        menu_never_sold(conn)
                    elif option == "10":
                        menu_backup(conn)
                    elif option == "0":
                        print("\nGoodbye!\n")
                        break
                    else:
                        print("Invalid Option. Please try again.")
                except ProductError as e:
                    print(e)
                except sqlite3.IntegrityError:
                    print("That change breaks a database rule")
                except sqlite3.Error:
                    print("There was a problem with the database")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!\n")

if __name__ == "__main__": 
    main()
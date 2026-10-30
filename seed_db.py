from contextlib import closing

from inventory_db import connect, create_schema, get_db_path


def seed(conn):
    suppliers = [
        (1, "Tools Inc", "555-0101", "contact@toolsinc.com"),
        (2, "MadeInChina", "555-0102", "sales@madeinchina.com"),
        (3, "BuildRight Supplies", "555-0103", "info@buildright.com"),
        (4, "PaintPro", "555-0104", "sales@paintpro.com"),
    ]

    products = [
        (1, "TOOL-Hammer", "Hammer", "Tool", 1, 1500, 25, 5),
        (2, "MAT-WoodPlank", "Wooden Plank", "Material", 2, 800, 100, 20),
        (3, "MAT-SteelSheet", "Steel Sheet", "Material", 2, 2500, 5, 10),
        (4, "TOOL-PhillipsScrewdriver", "Phillips Head Screwdriver",
         "Tool", 1, 1200, 30, 5),
        (5, "TOOL-Drill", "Electric Drill", "Tool", 1, 6500, 12, 5),
        (6, "MAT-Plywood", "Plywood Sheet", "Material", 2, 1800, 40, 10),
        (7, "FAST-Nails", "Box of Nails", "Fastener", 3, 500, 8, 8),
        (8, "FAST-WoodScrews", "Wood Screws", "Fastener", 3, 700, 15, 10),
        (9, "FAST-Bolts", "Steel Bolts", "Fastener", 3, 900, 4, 10),
        (10, "PAINT-White", "White Paint", "Paint", 4, 2200, 20, 5),
        (11, "PAINT-Blue", "Blue Paint", "Paint", 4, 2400, 3, 5),
        (12, "PAINT-Primer", "Wall Primer", "Paint", 4, 1900, 10, 5),
    ]

    sales = [
        (1, "2026-10-01T10:00:00"),
        (2, "2026-10-03T14:30:00"),
        (3, "2026-10-07T09:15:00"),
        (4, "2026-10-12T11:45:00"),
        (5, "2026-10-20T16:00:00"),
    ]

    sale_items = [
        (1, 1, 1, 2, 1500),
        (2, 1, 2, 5, 800),
        (3, 1, 7, 3, 500),

        (4, 2, 3, 2, 2500),
        (5, 2, 4, 1, 1200),
        (6, 2, 10, 2, 2200),

        (7, 3, 5, 1, 6500),
        (8, 3, 6, 4, 1800),

        (9, 4, 8, 3, 700),
        (10, 4, 11, 2, 2400),

        (11, 5, 1, 1, 1500),
        (12, 5, 2, 5, 800),
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO Suppliers
        (SupplierID, Name, Phone, Email)
        VALUES (?, ?, ?, ?)
    """, suppliers)

    conn.executemany("""
        INSERT OR IGNORE INTO Products
        (ProductID, SKU, Name, Category, SupplierID,
         UnitPrice, CurrentStock, ReorderLevel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    conn.executemany("""
        INSERT OR IGNORE INTO Sales
        (SaleID, SaleDateTime)
        VALUES (?, ?)
    """, sales)

    conn.executemany("""
        INSERT OR IGNORE INTO SaleItems
        (SaleItemID, SaleID, ProductID, Quantity, PriceAtSale)
        VALUES (?, ?, ?, ?, ?)
    """, sale_items)

    conn.commit()


def main():
    path = get_db_path()
    with closing(connect(path)) as conn:
        create_schema(conn)
        seed(conn)

        for table in ["Suppliers", "Products", "Sales", "SaleItems", "StockMovements"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count}")


if __name__ == "__main__": 
    main()
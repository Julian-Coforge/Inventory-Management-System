

def seed(conn):
    suppliers = [
        (1, "Tools Inc", "555-0101", "contact@toolsinc.com"),
        (2, "MadeInChina", "555-0102", "sales@madeinchina.com"),
    ]

    products = [
        (1, "TOOL-Hammer", "Hammer", "Tool", 1, 1500, 25, 5),
        (2, "MAT-WoodPlank", "Wooden Plank", "Material", 2, 800, 100, 20),
        (3, "MAT-SteelSheet", "Steel Sheet", "Material", 2, 2500, 5, 10),
        (4, "TOOL-PhillipsScrewdriver", "Phillips Head Screwdriver",
         "Tool", 1, 1200, 30, 5),
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

    conn.commit()
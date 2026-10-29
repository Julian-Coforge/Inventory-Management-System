import sqlite3
from pathlib import Path


class ProductError(Exception):
    """Base for all product rule errors."""

class DuplicateSKUError(ProductError):
    pass

class UnknownSupplierError(ProductError):
    pass

class NegativePriceError(ProductError):
    pass

class NegativeQuantityError(ProductError):
    pass

class ProductHasSalesError(ProductError):
    pass

class UnknownSKUError(ProductError):
    pass

class EmptySaleError(ProductError):
    pass

def connect(path: str):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def create_schema(conn):
    sql = (Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(sql)

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

def add_product(conn, sku: str, name: str, category: str, supplier_id: int, unit_price: int, current_stock: int, reorder_level: int):
    
    if unit_price < 0:
        raise NegativePriceError("Price cannot be negative")
    if current_stock < 0:
        raise NegativeQuantityError("Stock cannot be negative")
    if reorder_level < 0:
        raise NegativeQuantityError("Reorder level cannot be negative")
    
    product_tuple = (sku, name, category, supplier_id, unit_price, current_stock, reorder_level)
    
    try:
        cursor = conn.execute(
            """INSERT INTO Products (SKU, Name, 
            Category, SupplierID, UnitPrice, CurrentStock, 
            ReorderLevel) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            product_tuple
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            raise DuplicateSKUError("That SKU already exists") from e
        if "FOREIGN KEY" in str(e):
            raise UnknownSupplierError("That supplier does not exist")
        raise

def get_product(conn, sku: str):
    product = conn.execute(
        """SELECT Products.* , Suppliers.Name AS SupplierName
        FROM Products 
        JOIN Suppliers ON Products.SupplierID = Suppliers.SupplierID
        WHERE Products.SKU = ?""",
        (sku,)
    ).fetchone()
    return product

def change_price(conn, sku: str, new_price: int):

    if new_price < 0:
        raise NegativePriceError("Price cannot be below zero")

    price_tuple = (new_price, sku)
    conn.execute(
        """UPDATE Products SET UnitPrice = ? WHERE SKU = ?""",
        price_tuple
    )
    conn.commit()

def delete_product(conn, sku: str):

    product = get_product(conn, sku)

    if product is None:
        raise UnknownSKUError("Cannot find product")

    count = conn.execute(
        """SELECT COUNT(*) FROM SaleItems WHERE ProductID = ?""",
        (product["ProductID"],)
    ).fetchone()[0]

    if count > 0:
        raise ProductHasSalesError("Cannot delete a product with sales history")
    
    conn.execute(
        """DELETE FROM Products WHERE SKU = ?""",
        (sku,)
    )
    conn.commit()

def search_products(conn, category=None, max_price=None, low_stock=False, text=None, in_stock=False):
    sql = """SELECT Products.* , Suppliers.Name AS SupplierName FROM Products 
            JOIN Suppliers ON Products.SupplierID = Suppliers.SupplierID"""
    conditions = []
    params = []
    if category is not None:
        conditions.append("Products.Category = ?")
        params.append(category)
    if max_price is not None:
        conditions.append("Products.UnitPrice <= ?")
        params.append(max_price)
    if text is not None:
        pattern = f"%{text}%"
        conditions.append("(Products.Name LIKE ? OR Products.SKU LIKE ? OR Suppliers.Name LIKE ?)")
        params.extend([pattern, pattern, pattern])
    if low_stock:
        conditions.append("Products.CurrentStock <= Products.ReorderLevel")
    if in_stock:
        conditions.append("Products.CurrentStock > 0")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY Products.Name"
    return conn.execute(sql, params).fetchall()

def record_sale(conn, items):

    for sku, quantity in items:
        if quantity <= 0:
            raise NegativeQuantityError("Quantity must be at least 1")
         
    if not items:
        raise EmptySaleError("The list has no items")
    
    with conn:
        cur = conn.execute("INSERT INTO Sales DEFAULT VALUES")
        sale_id = cur.lastrowid
        for sku, quantity in items:
            product = get_product(conn, sku)
            if product is None:
                raise UnknownSKUError("Provided SKU does not match any in database")
            conn.execute(
                "UPDATE Products SET CurrentStock = CurrentStock - ? WHERE ProductID = ?",
                (quantity, product["ProductID"],),
            )
            conn.execute(
                "INSERT INTO SaleItems (SaleID, ProductID, Quantity, PriceAtSale) VALUES (?, ?, ?, ?)",
                (sale_id, product["ProductID"], quantity, product["UnitPrice"],)
            )
            conn.execute(
                "INSERT INTO StockMovements (ProductID, Change, Reason) VALUES (?, ?, ?)",
                (product["ProductID"], -quantity, 'sale')
            )
    return sale_id
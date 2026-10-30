import os
import sqlite3
from datetime import datetime
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

class NoChangeError(ProductError):
    pass

class AdjustBelowZeroError(ProductError):
    pass

class DuplicateSaleLineError(ProductError):
    pass

DEFAULT_DB = Path(__file__).parent / "inventory.db"

def get_db_path():
    return os.environ.get("INVENTORY_DB", str(DEFAULT_DB))

def connect(path: str):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def create_schema(conn):
    sql = (Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(sql)

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

def record_sale(conn, items, when=None):

    if not items:
        raise EmptySaleError("The list has no items")

    for sku, quantity in items:
        if quantity <= 0:
            raise NegativeQuantityError("Quantity must be at least 1")

    if when is None:
        when = datetime.now().isoformat()

    skus = [sku for sku, quantity in items]

    if len(skus) != len(set(skus)):
        raise DuplicateSaleLineError("Duplicate product detected")
    
    with conn:
        cur = conn.execute("INSERT INTO Sales (SaleDateTime) VALUES (?)", (when,))
        sale_id = cur.lastrowid
        for sku, quantity in items:
            product = get_product(conn, sku)
            if product is None:
                raise UnknownSKUError(f"No product {sku}")
            conn.execute(
                "UPDATE Products SET CurrentStock = CurrentStock - ? WHERE ProductID = ?",
                (quantity, product["ProductID"],),
            )
            conn.execute(
                "INSERT INTO SaleItems (SaleID, ProductID, Quantity, PriceAtSale) VALUES (?, ?, ?, ?)",
                (sale_id, product["ProductID"], quantity, product["UnitPrice"],)
            )
            conn.execute(
                "INSERT INTO StockMovements (ProductID, Change, Reason, WhenHappened) VALUES (?, ?, ?, ?)",
                (product["ProductID"], -quantity, 'sale', when,)
            )
    return sale_id

def stock_value_by_supplier_report(conn):
    result = conn.execute(
            """SELECT Suppliers.Name AS SupplierName,
            SUM(Products.UnitPrice * Products.CurrentStock)
            AS StockValue FROM Products JOIN Suppliers 
            ON Products.SupplierID = Suppliers.SupplierID
            GROUP BY Suppliers.SupplierID
            ORDER BY StockValue DESC"""
        ).fetchall()

    return result

def low_stock_report(conn):
    result = conn.execute(
            """SELECT Products.SKU AS ProductSKU, Products.Name, Products.CurrentStock,
            Products.ReorderLevel, Products.ReorderLevel - Products.CurrentStock AS UnitsShort
            FROM Products WHERE Products.CurrentStock <= Products.ReorderLevel
            ORDER BY UnitsShort DESC"""
        ).fetchall()

    return result

def sales_by_product_report(conn):
    result = conn.execute(
            """SELECT Products.SKU AS ProductSKU, Products.Name,
            SUM(SaleItems.Quantity) AS UnitsSold,
            SUM(SaleItems.Quantity * SaleItems.PriceAtSale) AS Revenue
            FROM SaleItems JOIN Products ON SaleItems.ProductID = Products.ProductID
            GROUP BY Products.ProductID ORDER BY Revenue DESC"""
        ).fetchall()

    return result

def never_sold_report(conn):
    result = conn.execute(
            """SELECT Products.SKU AS ProductSKU, Products.Name
            FROM Products LEFT JOIN SaleItems ON Products.ProductID = SaleItems.ProductID
            WHERE SaleItems.SaleItemID IS NULL ORDER BY Products.Name"""
        ).fetchall()

    return result

def restock(conn, sku, amount, when=None):
    if amount <= 0:
        raise NegativeQuantityError("Restock amount must be at least 1")

    product = get_product(conn, sku)
    if product is None:
        raise UnknownSKUError(f"No product {sku}")
    if when is None:
        when = datetime.now().isoformat()
    with conn:
        conn.execute(
            "UPDATE Products SET CurrentStock = CurrentStock + ? WHERE ProductID = ?",
            (amount, product["ProductID"]),
        )
        conn.execute(
            "INSERT INTO StockMovements (ProductID, Change, Reason, WhenHappened) VALUES (?, ?, ?, ?)",
            (product["ProductID"], amount, "restock", when),
        )

def adjust(conn, sku, change, when=None):
    if change == 0:
        raise NoChangeError("Change is 0, log would be useless")

    product = get_product(conn, sku)
    if product is None:
        raise UnknownSKUError(f"No product {sku}")

    if product["CurrentStock"] + change < 0:
        raise AdjustBelowZeroError("Adjustment would make stock negative")

    if when is None:
        when = datetime.now().isoformat()
    with conn:
        conn.execute(
            "UPDATE Products SET CurrentStock = CurrentStock + ? WHERE ProductID = ?",
            (change, product["ProductID"]),
        )
        conn.execute(
            "INSERT INTO StockMovements (ProductID, Change, Reason, WhenHappened) VALUES (?, ?, ?, ?)",
            (product["ProductID"], change, "adjustment", when),
        )

def backup(conn, path):
    dest = sqlite3.connect(path)
    try:
        conn.backup(dest)
    finally:
        dest.close()
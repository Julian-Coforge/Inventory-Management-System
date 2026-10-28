

CREATE TABLE IF NOT EXISTS Suppliers(
    SupplierID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE,
    Phone TEXT,
    Email TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS Products(
    ProductID INTEGER PRIMARY KEY,
    SKU TEXT NOT NULL UNIQUE,
    Name TEXT NOT NULL,
    Category TEXT NOT NULL,
    SupplierID INTEGER NOT NULL REFERENCES Suppliers(SupplierID),
    UnitPrice INTEGER NOT NULL CHECK (UnitPrice >= 0),
    CurrentStock INTEGER NOT NULL CHECK (CurrentStock >= 0),
    ReorderLevel INTEGER NOT NULL CHECK (ReorderLevel >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS Sales(
    SaleID INTEGER PRIMARY KEY,
    SaleDateTime TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS SaleItems(
    SaleItemID INTEGER PRIMARY KEY,
    SaleID INTEGER NOT NULL REFERENCES Sales(SaleID),
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Quantity INTEGER NOT NULL CHECK (Quantity > 0),
    PriceAtSale INTEGER NOT NULL CHECK (PriceAtSale >= 0),
    UNIQUE (ProductID, SaleID)
) STRICT;

CREATE TABLE IF NOT EXISTS StockMovements(
    MovementID INTEGER PRIMARY KEY,
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Change INTEGER NOT NULL,
    Reason TEXT NOT NULL CHECK (Reason IN ()'restock', 'adjustment', 'sale')),
    WhenHappened TEXT NOT NULL
) STRICT;
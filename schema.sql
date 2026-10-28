

CREATE TABLE IF NOT EXISTS Suppliers(
    SupplierID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE,
    Phone TEXT,
    Email TEXT
);

CREATE TABLE IF NOT EXISTS Products(
    ProductID INTEGER PRIMARY KEY,
    SKU TEXT NOT NULL UNIQUE,
    Name TEXT NOT NULL,
    Category TEXT NOT NULL,
    SupplierID INTEGER NOT NULL REFERENCES Suppliers(SupplierID),
    UnitPrice INTEGER NOT NULL (UnitPrice CHECK >= 0),
    CurrentStock INTEGER NOT NULL (CurrentStock CHECK >= 0),
    ReorderLevel INTEGER NOT NULL (ReorderLevel CHECK >= 0)
);

CREATE TABLE IF NOT EXISTS Sales(
    SaleID INTEGER PRIMARY KEY,
    SaleDateTime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS SaleItems(
    SaleItemID INTEGER PRIMARY KEY,
    SaleID INTEGER NOT NULL REFERENCES Sales(SaleID),
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Quantity INTEGER NOT NULL (Quantity CHECK > 0),
    PriceAtSale INTEGER NOT NULL (PriceAtSale CHECK >= 0)
);

CREATE TABLE IF NOT EXISTS StockMovements(
    MovementID INTEGER PRIMARY KEY,
    ProductID INTEGER NOT NULL REFERENCES Products(ProductID),
    Change INTEGER NOT NULL,
    Reason TEXT NOT NULL CHECK IN ('restock', 'adjustment', 'sale'),
    WhenHappened TEXT NOT NULL
);
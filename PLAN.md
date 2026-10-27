# Inventory Management System

## Objective
- The aim of this project is to build a management system for the stock of a small hardware store.
- Data is stored in an SQLite database with related tables for:
    - Suppliers, products, sales, the items in each sale, and a log of every stock movement.

## Tables and relationships

Notes:
- All tables are STRICT, and use IF NOT EXISTS
- conenct() turns PRAGMA foreign_keys = ON for every connection

- Suppliers
    - One row = one company the store buys stock from
    - Links into Products in a one-to-many relationship (a supplier may have many products)
    - Columns:
        - SupplierID: INTEGER, PRIMARY KEY
            - Why: a stable id that never changes, so products can point at it
        - Name: TEXT, NOT NULL, UNIQUE
            - Why NOT NULL: reports and search show the supplier name, so it can't be empty
            - Why UNIQUE: two suppliers with the same name would make the
              "stock value by supplier" report ambiguous
        - Phone: TEXT, optional (can be NULL)
            - Why TEXT: phone numbers have leading zeros and "+", and you never do maths on them
        - Email: TEXT, optional (can be NULL)
    - Delete rule: a supplier with products can't be deleted, because
      products.SupplierID points at it and foreign keys are on

- Products
    - One row = one product the store sells
    - Links from Suppliers (many products per supplier); links into Sale Items and Stock Movements (one-to-many each)
    - Columns:
        - ProductID: INTEGER, PRIMARY KEY
            - Why: stable id; add_product returns it; other tables point at it
        - SKU: TEXT, NOT NULL, UNIQUE
            - Why: the store's own product code; two products can't share one (duplicate SKU error)
        - Name: TEXT, NOT NULL
        - Category: TEXT, NOT NULL
            - Why: search filters and grouping need it
        - SupplierID: INTEGER, NOT NULL, REFERENCES Suppliers(SupplierID)
            - Why: every product has a real supplier (unknown supplier error)
        - Unit Price: INTEGER (cents), NOT NULL, CHECK >= 0
            - Why: whole cents avoid float rounding; a price can't be negative
        - Current Stock: INTEGER, NOT NULL, CHECK >= 0
            - Why: you can't hold fewer than zero items; this makes an over-sale fail
        - Reorder level: INTEGER, NOT NULL, CHECK >= 0
            - Why: low-stock report compares stock against it
    - Delete rule: a product with sale items can't be deleted, because Sale Items points at it

- Sales
    - One row = one checkout
    - Links into Sale Items (one-to-many)
    - Columns:
        - SaleID: INTEGER, PRIMARY KEY
        - Sale Date/Time: TEXT, NOT NULL, ISO 8601 (e.g. 2026-10-27T14:30:00)
            - Why: SQLite has no date type; ISO text sorts correctly; tests pass a fixed time
    - No total column: totals are calculated from Sale Items so they can never disagree

- Sale Items
    - One row = one product line within one sale
    - Junction table between Sales and Products (many-to-many)
    - Columns:
        - SaleItemID: INTEGER, PRIMARY KEY
        - SaleID: INTEGER, NOT NULL, REFERENCES Sales(SaleID)
        - ProductID: INTEGER, NOT NULL, REFERENCES Products(ProductID)
        - Quantity: INTEGER, NOT NULL, CHECK > 0
            - Why: a line selling zero or negative items makes no sense
        - Price at time of sale: INTEGER (cents), NOT NULL, CHECK >= 0
            - Why: product prices change; the sale must keep what was actually charged
    - UNIQUE (SaleID, ProductID)
        - Why: the same product twice in one sale is refused by the database itself
    - Index on ProductID
        - Why: the sales-by-product and never-sold reports join on it

- Stock Movements
    - One row = one change to one product's stock
    - Links from Products (one product, many movements)
    - Columns:
        - MovementID: INTEGER, PRIMARY KEY
        - ProductID: INTEGER, NOT NULL, REFERENCES Products(ProductID)
        - Change: INTEGER, NOT NULL (signed, no >= 0 check)
            - Why: + for restock, - for sale or damage; the sign shows the direction
        - Reason: TEXT, NOT NULL, CHECK IN ('restock', 'adjustment', 'sale')
            - Why: only the three reasons the brief allows
        - When it happened: TEXT, NOT NULL, ISO 8601
    - Index on ProductID
        - Why: looking up a product's movement history
    - Starts empty; rows are only added by restock, adjust and record a sale


## Public Functions

Every function takes the connection first, so tests can pass an in-memory database.
Stock functions take `when` (ISO time text), defaulting to now.

| Name | Inputs | Returns | Errors |
|---|---|---|---|
| connect | path (optional; falls back to INVENTORY_DB, then a file next to the code) | Connection with foreign keys on and rows readable by column name | – |
| add_product | conn, sku, name, category, supplier_id, price_cents, quantity, reorder_level | new product id | IntegrityError: duplicate SKU, unknown supplier, negative price or quantity |
| get_product | conn, product_id | one row with the supplier's name (join), or None | – |
| change_price | conn, product_id, new_price_cents | True if changed, False if no such product | IntegrityError: negative price |
| delete_product | conn, product_id | True if deleted, False if no such product | IntegrityError: product has sales history |
| search_products | conn, text, category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False | list of rows sorted by name | – |
| stock_value_by_supplier | conn | rows: supplier name, total value in cents, highest first | – |
| low_stock_report | conn | rows: product, stock, reorder level, units short | – |
| sales_by_product | conn | rows: product, units sold, revenue in cents, highest revenue first | – |
| never_sold | conn | rows: products with no sale items | – |
| restock | conn, product_id, amount, when=None | new stock level | ValueError: amount <= 0 or unknown product |
| adjust_stock | conn, product_id, change, when=None | new stock level | ValueError: unknown product; IntegrityError: stock would go negative |
| record_sale | conn, items (list of (product_id, quantity)), when=None | new sale id | ValueError: unknown product; IntegrityError: not enough stock, same product twice |
| backup_database | conn, destination path | None | sqlite3.Error if the copy fails |

## Transactions

All multi-step changes run inside one `with conn:` block. If the block finishes, everything
commits together. If any error is raised inside it, everything rolls back. Helper functions
used inside the block never call commit themselves.

### Restock(product_id, amount, when)
Checks before writing:
1. amount must be > 0, otherwise ValueError (nothing written)
2. product must exist, otherwise ValueError
Inside `with conn:`:
3. Add amount to the product's stock
4. Insert a stock movement: +amount, reason 'restock', when
If step 3 or 4 fails: rollback, stock unchanged, no movement logged.

### Adjust(product_id, change, when)
Checks before writing:
1. product must exist, otherwise ValueError
Inside `with conn:`:
2. Add change (may be negative) to the product's stock.
   If stock would drop below 0, the CHECK (stock >= 0) raises IntegrityError
3. Insert a stock movement: change, reason 'adjustment', when
If step 2 or 3 fails: rollback, stock unchanged, no movement logged.

### Record sale(items, when)
items = list of (product_id, quantity)
Inside `with conn:`:
1. Insert a sale row with when, and keep its new sale id
2. For each (product_id, quantity):
   a. Look up the product's current price. Not found: raise ValueError
   b. Insert a sale item: sale id, product id, quantity, current price.
      Same product twice: the UNIQUE (SaleID, ProductID) raises IntegrityError
   c. Subtract quantity from the product's stock.
      Not enough stock: the CHECK (stock >= 0) raises IntegrityError
   d. Insert a stock movement: -quantity, reason 'sale', when
3. Block ends with no error: commit, return the sale id
If any line fails (for example line 2 of 3): the error leaves the `with` block, so SQLite
rolls back everything since step 1. Afterwards there is no sale row, no sale items, no
movements, and every product's stock is what it was before. The error is passed up to
the menu, which shows a friendly message.

## Release Plan

### v1.0.0
1. Merge feature/menu-and-container with CI green (tests plus docker-build job)
2. Add the 1.0.0 entry to CHANGELOG.md
3. Tag main as v1.0.0 and push the tag to GitHub
4. Build the Docker image tagged 1.0.0
5. Run it with a named volume, INVENTORY_DB pointing inside the volume.
   Seed it, stop it, start a new container on the same volume, and check the data is still there

### v1.1.0
1. Branch feature/low-stock-banner from main
2. Write a test first: the banner shows the number of products at or below their reorder level
3. Add the banner to the start of the menu, open a PR, merge with CI green
4. Add the 1.1.0 entry to CHANGELOG.md, tag v1.1.0, build the image tagged 1.1.0

### Upgrade, backup and rollback
1. Before upgrading, back up the database with SQLite's backup function
2. Check the backup: PRAGMA integrity_check returns "ok" and every table's row count
   matches the original
3. Run 1.1.0 on the same volume and confirm the banner appears
4. Roll back: stop 1.1.0, run the 1.0.0 image on the same volume, and confirm the row counts
   are unchanged. This is safe because 1.1.0 makes no schema changes
5. Restore if needed: with no container running, copy the backup file over the database file
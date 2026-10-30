# Inventory Management System

This is a stock system for a small hardware store. It keeps suppliers, products, sales, and stock movements in a SQLite database, and a text menu is used to search the catalogue, record sales, restock, and print reports. It is meant for someone working the counter or checking what needs to be reordered, not for a large warehouse.

## Requirements

- Python 3.14. This project was written and tested on Python 3.14.10. CI uses 3.14, and the Docker image is `python:3.14.10-slim`.
- SQLite 3.37 or newer. The tables are `STRICT`, which SQLite added in 3.37. The Python on this machine is linked to SQLite 3.50.4.
- Docker Desktop, for building the image and running it with a volume.

## How to run locally

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_db.py
python main.py
```

`seed_db.py` creates the tables and loads the sample data. `main.py` does that again on startup, then opens the menu. `INSERT OR IGNORE` means running either command twice does not duplicate the sample rows.

## Configuration

`INVENTORY_DB` is the path to the database file. `get_db_path()` reads that variable. If it is not set, the program uses `inventory.db` in the same folder as the code.

Docker sets `INVENTORY_DB=/data/inventory.db`. A volume mounted at `/data` is what keeps the file when the container stops.

## Running tests

With the virtual environment active:

```bash
pytest
ruff check .
```

`pytest` collects 40 tests and they all pass. `ruff check .` reports that all checks passed.

## Sample data

`python seed_db.py` prints one count per table. A second run prints the same counts, because the inserts are ignored when the rows are already there.

```text
python seed_db.py
Suppliers: 4
Products: 12
Sales: 5
SaleItems: 12
StockMovements: 0

python seed_db.py
Suppliers: 4
Products: 12
Sales: 5
SaleItems: 12
StockMovements: 0
```

That is 4 suppliers, 12 products, 5 sales, 12 sale lines, and no stock movements. The sample sales were inserted directly, so they did not write movement rows.

## Expected report results

Prices are stored as whole cents. The menu divides by 100 and prints dollars to 2 decimal places. These are the four reports on the sample data, before any extra sale.

Stock value by supplier, highest first:

| Supplier | Value |
|---|---:|
| MadeInChina | $1645.00 |
| Tools Inc | $1515.00 |
| PaintPro | $702.00 |
| BuildRight Supplies | $181.00 |

Low stock (stock at or below the reorder level), most short first:

| SKU | Name | Stock | Reorder | Short |
|---|---|---:|---:|---:|
| FAST-Bolts | Steel Bolts | 4 | 10 | 6 |
| MAT-SteelSheet | Steel Sheet | 5 | 10 | 5 |
| PAINT-Blue | Blue Paint | 3 | 5 | 2 |
| FAST-Nails | Box of Nails | 8 | 8 | 0 |

Sales by product, highest revenue first:

| SKU | Name | Units | Revenue |
|---|---|---:|---:|
| MAT-WoodPlank | Wooden Plank | 10 | $80.00 |
| MAT-Plywood | Plywood Sheet | 4 | $72.00 |
| TOOL-Drill | Electric Drill | 1 | $65.00 |
| MAT-SteelSheet | Steel Sheet | 2 | $50.00 |
| PAINT-Blue | Blue Paint | 2 | $48.00 |
| TOOL-Hammer | Hammer | 3 | $45.00 |
| PAINT-White | White Paint | 2 | $44.00 |
| FAST-WoodScrews | Wood Screws | 3 | $21.00 |
| FAST-Nails | Box of Nails | 3 | $15.00 |
| TOOL-PhillipsScrewdriver | Phillips Head Screwdriver | 1 | $12.00 |

Never sold:

| SKU | Name |
|---|---|
| FAST-Bolts | Steel Bolts |
| PAINT-Primer | Wall Primer |

## A failed sale, halfway

Before the sale, a lookup showed Hammer (`TOOL-Hammer`) with stock 25 and Steel Sheet (`MAT-SteelSheet`) with stock 5.

The sale was 1 Hammer and 999 Steel Sheets, entered as menu option 5:

```text
Enter product SKU (or Enter to finish): TOOL-Hammer
Enter quantity: 1
Enter product SKU (or Enter to finish): MAT-SteelSheet
Enter quantity: 999
Enter product SKU (or Enter to finish):
That change breaks a database rule
```

Afterwards, Hammer was still 25 and Steel Sheet was still 5.

`record_sale` inserts the sale, then each line, inside one `with conn:` block. The Hammer line is written first, and the Steel Sheet update then fails the check that stock cannot go below zero. Leaving that block on an error makes SQLite roll the whole sale back, so the Hammer change does not stay either.

## Docker

Build the 1.1.0 image from the project folder:

```bash
docker build --no-cache -t inventory:1.1.0 .
```

```text
[+] Building 7.0s (11/11) FINISHED                                                        docker:desktop-linux
 => [internal] load build definition from Dockerfile                                      0.0s
 => [internal] load metadata for docker.io/library/python:3.14.10-slim                    0.4s
 => [internal] load .dockerignore                                                         0.0s
 => [1/6] FROM docker.io/library/python:3.14.10-slim                                      0.0s
 => [internal] load build context                                                         0.0s
 => CACHED [2/6] WORKDIR /app                                                             0.0s
 => [3/6] COPY requirements.txt .                                                         0.0s
 => [4/6] RUN pip install --no-cache-dir -r requirements.txt                              4.4s
 => [5/6] COPY . .                                                                        0.0s
 => [6/6] RUN mkdir -p /data                                                              0.1s
 => exporting to image                                                                    2.0s
 => => naming to docker.io/library/inventory:1.1.0                                        0.0s
 => => unpacking to docker.io/library/inventory:1.1.0                                     0.3s
```

Run it with an interactive terminal and a named volume:

```bash
docker run -it --rm -v inventory-data:/data inventory:1.1.0
```

The 1.0.0 image is the same command with `inventory:1.0.0`. It is the program before the low-stock banner.

## Persistence check

Both runs used the volume `inventory-data`.

First run, on `inventory:1.1.0`. The banner printed `4 products are at or below their reorder level.` Option 3 added a product, then option 0 quit:

```text
Enter product SKU: TEST-Persistance
Enter product name: Persistant Item
Enter product category: Test
Enter supplier ID: 1
Enter unit price in pence: 1000
Enter current stock: 1000
Enter reorder level: 50
Added Persistant Item (ID 13)
```

Second run, a new container on the same volume. Option 2 looked that SKU up again:

```text
Enter product SKU: TEST-Persistance

RESULT FOUND:
SKU: TEST-Persistance
Name: Persistant Item
Category: Test
Supplier: Tools Inc
Unit Price: $10.00
Current Stock: 1000
Reorder Level: 50
```

The row was still there after the first container exited. Startup seeds with `INSERT OR IGNORE`, so it did not wipe the product that had been added.

## Releases and rollback

| Tag | Image | What it is |
|---|---|---|
| `v1.0.0` | `inventory:1.0.0` | Menu, reports, and Docker. Merge of pull request #7. |
| `v1.1.0` | `inventory:1.1.0` | Same program, plus the low-stock banner. Merge of pull request #8. |

To roll back, stop the 1.1.0 container and start the 1.0.0 image on the same volume:

```bash
docker run -it --rm -v inventory-data:/data inventory:1.0.0
```

That run opened straight onto the menu. The low-stock banner was not printed. Searching for `Test` still found the product added under 1.1.0:

```text
 RESULT FOUND: TEST-Persistance Persistant Item $10.00 1000
```

The row counts are unchanged because 1.1.0 does not change the schema. The banner is only a query printed at startup.

## Backup and restore

Menu option 10 copies the open database with SQLite's backup function. The file is named `backup-YYYYMMDD-HHMMSS.db` and is written next to the database file. The check below used `backup-20261030-162135.db`.

To restore, quit the program so nothing has the file open, copy the backup over `inventory.db`, and start `python main.py` again. In Docker, copy it over `/data/inventory.db` in the volume while no container is using it.

The backup passed the integrity check, and its row counts matched the original database:

```text
sqlite3 backup-20261030-162135.db "PRAGMA integrity_check;"
ok

sqlite3 inventory.db "SELECT COUNT(*) FROM Products;"
12

sqlite3 backup-20261030-162135.db "SELECT COUNT(*) FROM Products;"
12

sqlite3 backup-20261030-162135.db "SELECT COUNT(*) FROM Sales;"
5

sqlite3 backup-20261030-162135.db "SELECT COUNT(*) FROM Suppliers;"
4

sqlite3 backup-20261030-162135.db "SELECT COUNT(*) FROM SaleItems;"
12

sqlite3 backup-20261030-162135.db "SELECT COUNT(*) FROM StockMovements;"
0
```

## Changes from the brief

The table and column names are CamelCase, such as `Suppliers`, `SaleItems`, and `SupplierID`. The schema was taken from `PLAN.md`, which already used those names, so the SQL followed the plan instead of snake_case names.

The work was split into eight pull requests on `feature/database-and-seed`, `feature/products`, `feature/search`, `feature/reports`, `feature/stock-changes-and-sales`, `feature/menu`, `feature/container`, and `feature/low-stock-banner`. The plan named one branch, `feature/menu-and-container`, for the menu and Docker together. Those were split so each review stayed on one piece of the program.

`PLAN.md` passes `product_id` into `get_product`, `change_price`, `delete_product`, `restock`, `adjust_stock`, and `record_sale`. The code takes a SKU instead. The menu asks for the code printed on the product, and the functions use that same SKU so the counter does not have to look up a numeric id first.

## Self-review

If I started this again, I would follow the brief's names on the first day. The CamelCase tables and the extra branch names are now a deviations section, and they did not buy anything. One `feature/menu-and-container` branch, with the table names the brief asked for, would have made the schema, the plan, and this write-up say the same thing.

I would also write the test before the function every time, not only for the later features. The database tests and the sale rollback test earned their place, but several product tests arrived after the function already worked. That made it easier to bend the test around the code. Writing the stock-cannot-go-negative case first would have fixed the sale behaviour before the menu existed.

I would pick one currency symbol at the start and keep it. Amounts are cents in the database, which is the right way to store them, but the lookup screen printed pounds until the container work switched the menu to dollars. One symbol from the first print statement would have avoided that.

The part I would ask a reviewer to check is `adjust`. The function is implemented and tested, and a zero change or a change that would take stock below zero is rejected before anything is written. The menu never offers it. Option 4 is restock only. I am not sure that matches the brief, which treats an adjustment as something the store can do, not only something the module can do.

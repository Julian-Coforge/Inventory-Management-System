from inventory_db import connect, create_schema


def test_foreign_keys_are_on():
    conn = connect(":memory:")
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1

def test_table_exists():
    conn = connect(":memory:")
    create_schema(conn)
    row = conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",("Products",),).fetchone()
    assert row is not None
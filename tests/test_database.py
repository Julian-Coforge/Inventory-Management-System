from inventory_db import connect


def test_foreign_keys_are_on():
    conn = connect(":memory:")
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1
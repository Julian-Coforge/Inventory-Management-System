# Conftest File
import pytest

from inventory_db import connect, create_schema
from seed_db import seed


@pytest.fixture
def inventory_database():
    conn = connect(":memory:")
    create_schema(conn)
    seed(conn)
    return conn
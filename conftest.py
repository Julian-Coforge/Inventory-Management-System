# Conftest File
import pytest

from seed_db import seed
from inventory_db import connect, create_schema


@pytest.fixture
def inventory_database():
    conn = connect(":memory:")
    create_schema(conn)
    seed(conn)
    return conn
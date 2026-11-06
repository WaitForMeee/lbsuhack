import pytest


@pytest.fixture(autouse=True)
def database_state(reset_database):
    """Only database-backed suites prepare and seed the isolated test database."""

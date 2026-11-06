"""Never import app settings before selecting an isolated test database."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url

TEST_ROOT = Path(tempfile.mkdtemp(prefix="talenthub-test-"))
TEST_URL = os.environ.get(
    "TALENTHUB_TEST_DATABASE_URL", f"sqlite+pysqlite:///{TEST_ROOT / 'api.db'}"
)
url = make_url(TEST_URL)
if url.get_backend_name() != "sqlite" and not (url.database or "").startswith(
    "talenthub_test"
):
    raise RuntimeError(
        "Refusing tests: PostgreSQL database name must start with talenthub_test"
    )
os.environ["DATABASE_URL"] = TEST_URL
os.environ["DATABASE_SCHEMA"] = (
    "test_" + uuid4().hex if url.get_backend_name() == "postgresql" else "talenthub_v2"
)
os.environ["JWT_SECRET"] = "isolated-test-secret-with-more-than-thirty-two-characters"
os.environ["TRUSTED_ORIGINS"] = "http://frontend.test"


pytest_plugins = ["tests.support.database"]

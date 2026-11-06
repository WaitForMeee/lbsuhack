import os
import subprocess
import sys
from pathlib import Path

from app.db.session import engine
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[2]


def alembic(db_path, *args):
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT,
        env={
            **os.environ,
            "DATABASE_URL": f"sqlite+pysqlite:///{db_path}",
        },
        capture_output=True,
        text=True,
    )


def test_migration_upgrade_seed_repeat_and_downgrade(tmp_path):
    db = tmp_path / "migration.db"
    result = alembic(db, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    migrated = create_engine(f"sqlite+pysqlite:///{db}")
    assert set(inspect(migrated).get_table_names()) >= {
        "users",
        "parent_links",
        "notifications",
        "partnership_responses",
    }
    assert alembic(db, "check").returncode == 0
    for _ in range(2):
        seed = subprocess.run(
            [sys.executable, "-m", "app.scripts.seed_demo"],
            cwd=ROOT,
            env={**os.environ, "DATABASE_URL": f"sqlite+pysqlite:///{db}"},
            capture_output=True,
            text=True,
        )
        assert seed.returncode == 0, seed.stderr
    with migrated.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM users")) == 11
    result = alembic(db, "downgrade", "base")
    assert result.returncode == 0, result.stderr
    assert inspect(migrated).get_table_names() == ["alembic_version"]
    migrated.dispose()


def test_initial_migration_refuses_existing_product_tables(tmp_path):
    db = tmp_path / "existing.db"
    existing = create_engine(f"sqlite+pysqlite:///{db}")
    with existing.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE old_product (id INTEGER PRIMARY KEY)")
        conn.exec_driver_sql("INSERT INTO old_product VALUES (1)")
    result = alembic(db, "upgrade", "head")
    assert result.returncode != 0
    assert "requires a new empty database/schema" in result.stderr
    with existing.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM old_product")) == 1
    existing.dispose()


def test_model_and_migrated_constraints_match():
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.db.base import Base

    with engine.connect() as conn:
        changes = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert changes == []


def test_upgrade_preserves_parent_link_and_existing_partnership_response(tmp_path):
    from app.scripts.seed_demo import demo_id

    path = tmp_path / "upgrade.db"
    result = alembic(path, "upgrade", "20261106_0001")
    assert result.returncode == 0, result.stderr
    seed = subprocess.run(
        [sys.executable, "-m", "app.scripts.seed_demo"],
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": f"sqlite+pysqlite:///{path}"},
        capture_output=True,
        text=True,
    )
    assert seed.returncode == 0, seed.stderr
    db = create_engine(f"sqlite+pysqlite:///{path}")

    def id(key):
        return demo_id(key).hex

    with db.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO parent_links (parent_user_id,student_user_id,linked_at) VALUES (:parent,:student,CURRENT_TIMESTAMP)"
            ),
            {"parent": id("user:olga"), "student": id("user:alina")},
        )
        connection.execute(
            text(
                "INSERT INTO partnership_responses (id,request_id,school_id,status,created_at) VALUES (:id,:request,:school,'accepted',CURRENT_TIMESTAMP)"
            ),
            {
                "id": id("response:existing"),
                "request": id("partnership:market"),
                "school": id("org:school"),
            },
        )
    result = alembic(path, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    with db.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM parent_children")) == 1
        assert connection.scalar(
            text("SELECT responder_org_id FROM partnership_responses")
        ) == id("org:school")
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    assert alembic(path, "check").returncode == 0
    db.dispose()

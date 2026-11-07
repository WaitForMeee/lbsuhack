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
    # Public school offers belong to v2.2 and cannot be downgraded to v2.1.
    with migrated.begin() as conn:
        conn.execute(
            text("DELETE FROM partnership_requests WHERE visibility='all_companies'")
        )
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


def test_invitation_migration_preserves_preexisting_accounts_and_families(tmp_path):
    path = tmp_path / "invitation-upgrade.db"
    assert alembic(path, "upgrade", "head").returncode == 0
    seeded = subprocess.run([sys.executable, "-m", "app.scripts.seed_demo"], cwd=ROOT,
        env={**os.environ, "DATABASE_URL": f"sqlite+pysqlite:///{path}"}, capture_output=True, text=True)
    assert seeded.returncode == 0, seeded.stderr
    database = create_engine(f"sqlite+pysqlite:///{path}")
    with database.connect() as connection:
        users = connection.execute(text("SELECT id, email, password_hash, organization_id FROM users ORDER BY id")).all()
        families = connection.execute(text("SELECT parent_user_id, student_user_id FROM parent_children")).all()
    assert alembic(path, "downgrade", "20261106_0002").returncode == 0
    result = alembic(path, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    with database.connect() as connection:
        assert connection.execute(text("SELECT id, email, password_hash, organization_id FROM users ORDER BY id")).all() == users
        assert connection.execute(text("SELECT parent_user_id, student_user_id FROM parent_children")).all() == families
        assert connection.scalar(text("SELECT COUNT(*) FROM family_invitations")) == 0
    database.dispose()


def test_upgrade_preserves_parent_link_and_existing_partnership_response(tmp_path):
    from app.scripts.seed_demo import demo_id

    path = tmp_path / "upgrade.db"
    result = alembic(path, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    seed = subprocess.run(
        [sys.executable, "-m", "app.scripts.seed_demo"],
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": f"sqlite+pysqlite:///{path}"},
        capture_output=True,
        text=True,
    )
    assert seed.returncode == 0, seed.stderr
    with create_engine(f"sqlite+pysqlite:///{path}").begin() as connection:
        connection.execute(
            text("DELETE FROM partnership_requests WHERE visibility='all_companies'")
        )
    result = alembic(path, "downgrade", "20261106_0001")
    assert result.returncode == 0, result.stderr
    db = create_engine(f"sqlite+pysqlite:///{path}")

    def id(key):
        return demo_id(key).hex

    with db.begin() as connection:
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


def test_existing_demo_tokens_are_ready_after_upgrade_without_reseeding(tmp_path):
    import hashlib
    from app.scripts.seed_demo import demo_id

    path = tmp_path / "existing-demo-tokens.db"
    result = alembic(path, "upgrade", "20261107_0003")
    assert result.returncode == 0, result.stderr
    environment = {**os.environ, "DATABASE_URL": f"sqlite+pysqlite:///{path}"}
    seeded = subprocess.run([sys.executable, "-m", "app.scripts.seed_demo"], cwd=ROOT,
        env=environment, capture_output=True, text=True)
    assert seeded.returncode == 0, seeded.stderr
    database = create_engine(environment["DATABASE_URL"])
    replacement = "custom-token-already-issued-by-moderator"
    with database.begin() as connection:
        # A previously deployed database contains users but no token credentials.
        connection.execute(text("UPDATE users SET organization_token_hash=NULL, credential_version=0 WHERE role IN ('school','company')"))
        # An explicitly rotated account must not regain its public demo credential.
        connection.execute(text("UPDATE users SET organization_token_hash=:digest, credential_version=7 WHERE id=:identity"),
            {"digest": hashlib.sha256(replacement.encode()).hexdigest(), "identity": demo_id("user:school2").hex})
        connection.execute(text("INSERT INTO users (id,email,password_hash,first_name,last_name,role,organization_id,is_active,created_at,credential_version) SELECT :identity,'custom.organization@example.org',password_hash,first_name,last_name,role,organization_id,is_active,created_at,0 FROM users WHERE id=:source"), {"identity":demo_id("user:custom-organization").hex,"source":demo_id("user:school").hex})
        before = connection.execute(text("SELECT id,email,password_hash,first_name,last_name,organization_id FROM users ORDER BY id")).all()
        families = connection.execute(text("SELECT parent_user_id,student_user_id FROM parent_children")).all()
    result = alembic(path, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    # Exercise real authentication after the exact deployment sequence: migrate, no seed.
    script = """
from fastapi.testclient import TestClient
from app.main import app
from app.scripts.seed_demo import DEMO_ORGANIZATION_TOKENS
with TestClient(app) as client:
    for key, role in [('school','school'), ('company','company'), ('academy','company')]:
        response = client.post('/api/v1/auth/organization-login', json={'token': DEMO_ORGANIZATION_TOKENS[key], 'expected_role': role})
        assert response.status_code == 200, (key, response.status_code, response.text)
    response = client.post('/api/v1/auth/organization-login', json={'token':'custom-token-already-issued-by-moderator', 'expected_role':'school'})
    assert response.status_code == 200, response.status_code
    response = client.post('/api/v1/auth/organization-login', json={'token':DEMO_ORGANIZATION_TOKENS['school2']})
    assert response.status_code == 401, response.status_code
"""
    checked = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=environment, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    with database.connect() as connection:
        assert connection.execute(text("SELECT id,email,password_hash,first_name,last_name,organization_id FROM users ORDER BY id")).all() == before
        assert connection.execute(text("SELECT parent_user_id,student_user_id FROM parent_children")).all() == families
        assert connection.scalar(text("SELECT credential_version FROM users WHERE id=:identity"), {"identity":demo_id("user:school2").hex}) == 7
        assert connection.scalar(text("SELECT organization_token_hash FROM users WHERE id=:identity"), {"identity":demo_id("user:custom-organization").hex}) is None
    assert alembic(path, "upgrade", "head").returncode == 0
    database.dispose()

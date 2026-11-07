"""Provision missing demo credentials in existing databases without rerunning the seed."""

import hashlib
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op

revision = "20261107_0004"
down_revision = "20261107_0003"
branch_labels = None
depends_on = None


def demo_id(key):
    return uuid5(NAMESPACE_URL, "talenthub:v2:demo:" + key)


def upgrade():
    users = sa.table(
        "users",
        sa.column("id", sa.Uuid()),
        sa.column("email", sa.String()),
        sa.column("role", sa.String()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("is_active", sa.Boolean()),
        sa.column("organization_token_hash", sa.String()),
        sa.column("credential_version", sa.Integer()),
    )
    connection = op.get_bind()
    for key, role in (
        ("school", "school"), ("company", "company"),
        ("school2", "school"), ("academy", "company"),
    ):
        token = "th_demo_" + key + "_" + hashlib.sha256(("talenthub-demo:" + key).encode()).hexdigest()
        connection.execute(
            users.update().where(
                users.c.id == demo_id("user:" + key),
                users.c.email == key + "@demo.by",
                users.c.role == role,
                users.c.organization_id == demo_id("org:" + key),
                users.c.is_active.is_(True),
                users.c.organization_token_hash.is_(None),
                users.c.credential_version == 0,
            ).values(
                organization_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                credential_version=1,
            )
        )


def downgrade():
    # Credentials may have been handed out already; never revoke them implicitly.
    pass

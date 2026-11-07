"""Add revocable family invitations and organization credentials without replacing accounts."""

import sqlalchemy as sa
from alembic import op

revision = "20261107_0003"
down_revision = "20261106_0002"
branch_labels = None
depends_on = None


def upgrade():
    # Adding columns directly avoids recreating users and its inbound foreign keys.
    op.add_column("users", sa.Column("organization_token_hash", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("credential_version", sa.Integer(), server_default="0", nullable=False))
    op.create_index("ix_users_organization_token_hash", "users", ["organization_token_hash"], unique=True)
    op.create_table(
        "family_invitations",
        sa.Column("parent_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("family_invitations")
    op.drop_index("ix_users_organization_token_hash", table_name="users")
    op.drop_column("users", "credential_version")
    op.drop_column("users", "organization_token_hash")

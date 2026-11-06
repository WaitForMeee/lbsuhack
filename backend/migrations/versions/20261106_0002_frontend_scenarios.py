"""Persist multi-child parent accounts and bidirectional public partnerships."""

import sqlalchemy as sa
from alembic import op

revision = "20261106_0002"
down_revision = "20261106_0001"
branch_labels = None
depends_on = None


def change_partnership_constraints(expand):
    # SQLite needs table recreation; temporarily disable FK enforcement while
    # preserving and restoring all existing rows and referencing response rows.
    sqlite = op.get_bind().dialect.name == "sqlite"
    if sqlite:
        with op.get_context().autocommit_block():
            op.execute("PRAGMA foreign_keys=OFF")
    with op.batch_alter_table("partnership_requests") as batch:
        batch.drop_constraint("ck_visibility", type_="check")
        batch.drop_constraint("ck_target", type_="check")
        batch.create_check_constraint(
            "ck_visibility",
            "visibility IN ('direct','all_schools','all_companies')"
            if expand
            else "visibility IN ('direct','all_schools')",
        )
        batch.create_check_constraint(
            "ck_target",
            "(visibility = 'direct' AND target_org_id IS NOT NULL) OR (visibility IN ('all_schools','all_companies') AND target_org_id IS NULL)"
            if expand
            else "(visibility = 'direct' AND target_org_id IS NOT NULL) OR (visibility = 'all_schools' AND target_org_id IS NULL)",
        )
    with op.batch_alter_table("partnership_responses") as batch:
        batch.drop_constraint(
            "uq_request_school" if expand else "uq_request_organization", type_="unique"
        )
        batch.alter_column(
            "school_id" if expand else "responder_org_id",
            new_column_name="responder_org_id" if expand else "school_id",
            existing_type=sa.Uuid(),
            existing_nullable=False,
        )
        batch.drop_index(
            "ix_partnership_responses_school_id"
            if expand
            else "ix_partnership_responses_responder_org_id"
        )
    with op.batch_alter_table("partnership_responses") as batch:
        column = "responder_org_id" if expand else "school_id"
        batch.create_unique_constraint(
            "uq_request_organization" if expand else "uq_request_school",
            ["request_id", column],
        )
        batch.create_index("ix_partnership_responses_" + column, [column])
    if sqlite:
        with op.get_context().autocommit_block():
            op.execute("PRAGMA foreign_keys=ON")


def upgrade():
    change_partnership_constraints(True)
    op.create_table(
        "parent_children",
        sa.Column(
            "parent_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "student_user_id",
            sa.Uuid(),
            sa.ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        "INSERT INTO parent_children (parent_user_id,student_user_id,linked_at) SELECT parent_user_id,student_user_id,linked_at FROM parent_links"
    )
    op.create_table(
        "child_suggestions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "parent_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_user_id",
            sa.Uuid(),
            sa.ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("events.id"), nullable=False),
        sa.UniqueConstraint(
            "parent_user_id",
            "student_user_id",
            "event_id",
            name="uq_parent_child_event",
        ),
    )
    for column in ("parent_user_id", "student_user_id", "event_id"):
        op.create_index("ix_child_suggestions_" + column, "child_suggestions", [column])


def downgrade():
    # Offers addressed to all companies cannot be represented by the old contract.
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM partnership_requests WHERE visibility='all_companies'"
            )
        )
        .scalar()
    ):
        raise RuntimeError("Cannot downgrade while public school offers exist")
    op.drop_table("child_suggestions")
    op.drop_table("parent_children")
    change_partnership_constraints(False)

"""TalentHub v2 clean initial schema

Revision ID: 20261106_0001
Revises:
Create Date: 2026-11-06 11:44:51.738597
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "20261106_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not context.is_offline_mode() and set(
        sa.inspect(op.get_bind()).get_table_names()
    ) - {"alembic_version"}:
        raise RuntimeError(
            "TalentHub v2 requires a new empty database/schema; do not stamp or upgrade the old database."
        )
    op.create_table(
        "interests",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=100), nullable=False),
        sa.Column("is_suggested", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_table(
        "organizations",
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("directions", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("kind IN ('school','company','academy')", name="ck_kind"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organizations_kind"), "organizations", ["kind"], unique=False
    )
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(role IN ('school','company') AND organization_id IS NOT NULL) OR (role NOT IN ('school','company') AND organization_id IS NULL)",
            name="ck_user_organization",
        ),
        sa.CheckConstraint(
            "role IN ('student','parent','school','company','moderator')",
            name="ck_role",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False
    )
    op.create_table(
        "events",
        sa.Column("organizer_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("project_kind", sa.String(length=100), nullable=True),
        sa.Column("grade_min", sa.Integer(), nullable=False),
        sa.Column("grade_max", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("registration_deadline", sa.Date(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("venue", sa.String(length=250), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("terms", sa.Text(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("format IN ('offline','online','hybrid')", name="ck_format"),
        sa.CheckConstraint(
            "kind = 'project' OR project_kind IS NULL", name="ck_project_kind"
        ),
        sa.CheckConstraint("kind IN ('olympiad','project')", name="ck_kind"),
        sa.CheckConstraint(
            "status IN ('pending','published','rejected','registration_closed','completed')",
            name="ck_status",
        ),
        sa.CheckConstraint(
            "7 <= grade_min AND grade_min <= grade_max AND grade_max <= 11",
            name="ck_grade_range",
        ),
        sa.CheckConstraint("capacity > 0", name="ck_capacity"),
        sa.CheckConstraint("registration_deadline <= event_date", name="ck_deadline"),
        sa.ForeignKeyConstraint(
            ["organizer_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_events_catalog", "events", ["status", "event_date"], unique=False
    )
    op.create_index(
        op.f("ix_events_organizer_id"), "events", ["organizer_id"], unique=False
    )
    op.create_table(
        "partnership_requests",
        sa.Column("sender_org_id", sa.Uuid(), nullable=False),
        sa.Column("target_org_id", sa.Uuid(), nullable=True),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("moderation_status", sa.String(length=20), nullable=False),
        sa.Column("direct_decision", sa.String(length=20), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(visibility = 'direct' AND target_org_id IS NOT NULL) OR (visibility = 'all_schools' AND target_org_id IS NULL)",
            name="ck_target",
        ),
        sa.CheckConstraint(
            "direct_decision IS NULL OR direct_decision IN ('accepted','declined')",
            name="ck_direct_decision",
        ),
        sa.CheckConstraint(
            "moderation_status IN ('pending','approved','rejected')",
            name="ck_moderation_status",
        ),
        sa.CheckConstraint(
            "visibility IN ('direct','all_schools')", name="ck_visibility"
        ),
        sa.CheckConstraint(
            "target_org_id IS NULL OR sender_org_id != target_org_id",
            name="ck_different_orgs",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sender_org_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_org_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_partnership_requests_moderation_status"),
        "partnership_requests",
        ["moderation_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_partnership_requests_sender_org_id"),
        "partnership_requests",
        ["sender_org_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_partnership_requests_target_org_id"),
        "partnership_requests",
        ["target_org_id"],
        unique=False,
    )
    op.create_table(
        "student_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.CheckConstraint("grade IS NULL OR grade BETWEEN 7 AND 11", name="ck_grade"),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_student_profiles_school_id"),
        "student_profiles",
        ["school_id"],
        unique=False,
    )
    op.create_table(
        "achievements",
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','confirmed','rejected')", name="ck_status"
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["student_profiles.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_achievements_status"), "achievements", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_achievements_student_user_id"),
        "achievements",
        ["student_user_id"],
        unique=False,
    )
    op.create_table(
        "event_interests",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("interest_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["interest_id"],
            ["interests.id"],
        ),
        sa.PrimaryKeyConstraint("event_id", "interest_id"),
    )
    op.create_table(
        "event_registrations",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('submitted','under_review','waitlisted','approved','rejected','cancelled')",
            name="ck_status",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["student_profiles.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "student_user_id", name="uq_event_student"),
    )
    op.create_index(
        op.f("ix_event_registrations_event_id"),
        "event_registrations",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_registrations_student_user_id"),
        "event_registrations",
        ["student_user_id"],
        unique=False,
    )
    op.create_table(
        "notifications",
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_key", sa.String(length=250), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('confirmation','deadline','interest','invite')", name="ck_type"
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["student_profiles.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_index(
        "ix_notification_feed",
        "notifications",
        ["student_user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "parent_links",
        sa.Column("parent_user_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["student_user_id"], ["student_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("parent_user_id"),
    )
    op.create_index(
        op.f("ix_parent_links_student_user_id"),
        "parent_links",
        ["student_user_id"],
        unique=False,
    )
    op.create_table(
        "partnership_responses",
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending','accepted','declined')", name="ck_status"
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["partnership_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", "school_id", name="uq_request_school"),
    )
    op.create_index(
        op.f("ix_partnership_responses_request_id"),
        "partnership_responses",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_partnership_responses_school_id"),
        "partnership_responses",
        ["school_id"],
        unique=False,
    )
    op.create_table(
        "student_interests",
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("interest_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["interest_id"],
            ["interests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"], ["student_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("student_user_id", "interest_id"),
    )


def downgrade() -> None:
    op.drop_table("student_interests")
    op.drop_index(
        op.f("ix_partnership_responses_school_id"), table_name="partnership_responses"
    )
    op.drop_index(
        op.f("ix_partnership_responses_request_id"), table_name="partnership_responses"
    )
    op.drop_table("partnership_responses")
    op.drop_index(op.f("ix_parent_links_student_user_id"), table_name="parent_links")
    op.drop_table("parent_links")
    op.drop_index("ix_notification_feed", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(
        op.f("ix_event_registrations_student_user_id"), table_name="event_registrations"
    )
    op.drop_index(
        op.f("ix_event_registrations_event_id"), table_name="event_registrations"
    )
    op.drop_table("event_registrations")
    op.drop_table("event_interests")
    op.drop_index(op.f("ix_achievements_student_user_id"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_status"), table_name="achievements")
    op.drop_table("achievements")
    op.drop_index(op.f("ix_student_profiles_school_id"), table_name="student_profiles")
    op.drop_table("student_profiles")
    op.drop_index(
        op.f("ix_partnership_requests_target_org_id"), table_name="partnership_requests"
    )
    op.drop_index(
        op.f("ix_partnership_requests_sender_org_id"), table_name="partnership_requests"
    )
    op.drop_index(
        op.f("ix_partnership_requests_moderation_status"),
        table_name="partnership_requests",
    )
    op.drop_table("partnership_requests")
    op.drop_index(op.f("ix_events_organizer_id"), table_name="events")
    op.drop_index("ix_events_catalog", table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_organizations_kind"), table_name="organizations")
    op.drop_table("organizations")
    op.drop_table("interests")

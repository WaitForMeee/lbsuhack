"""Add milestone one product entities.

Revision ID: 20261105_0002
Revises: 20261105_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20261105_0002"
down_revision = "20261105_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("region", sa.String(120), server_default="Минск", nullable=False))
    op.add_column("organizations", sa.Column("contact_email", sa.String(320), nullable=True))
    op.add_column("organizations", sa.Column("website_url", sa.String(500), nullable=True))
    op.add_column("organizations", sa.Column("directions", sa.Text(), server_default="", nullable=False))
    op.create_table("categories", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("slug", sa.String(80), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_table("student_profiles", sa.Column("user_id", sa.Uuid(), nullable=False), sa.Column("grade", sa.Integer(), nullable=False), sa.Column("region", sa.String(120), nullable=False), sa.Column("bio", sa.Text(), nullable=False), sa.CheckConstraint("grade >= 1 AND grade <= 11", name="ck_student_grade"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id"))
    op.create_table("student_interests", sa.Column("student_profile_id", sa.Uuid(), nullable=False), sa.Column("category_id", sa.Uuid(), nullable=False), sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.user_id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("student_profile_id", "category_id"))
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("slug", sa.String(180), nullable=False), sa.Column("organizer_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(220), nullable=False), sa.Column("summary", sa.String(400), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False), sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("format", sa.Enum("OFFLINE", "ONLINE", "HYBRID", name="event_format", native_enum=False), nullable=False), sa.Column("region", sa.String(120), nullable=False),
        sa.Column("venue", sa.String(220), nullable=True), sa.Column("address", sa.String(500), nullable=True), sa.Column("meeting_url", sa.String(1000), nullable=True),
        sa.Column("target_audience", sa.String(500), nullable=False), sa.Column("min_grade", sa.Integer(), nullable=False), sa.Column("max_grade", sa.Integer(), nullable=False),
        sa.Column("participation_terms", sa.Text(), nullable=False), sa.Column("capacity", sa.Integer(), nullable=True), sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "PUBLISHED", "CANCELLED", name="event_status", native_enum=False), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organizer_id"], ["organizations.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("slug"),
    )
    for column in ("organizer_id", "title", "starts_at", "region", "status"): op.create_index(f"ix_events_{column}", "events", [column], unique=False)
    op.create_index("ix_events_slug", "events", ["slug"], unique=True)
    op.create_table("event_categories", sa.Column("event_id", sa.Uuid(), nullable=False), sa.Column("category_id", sa.Uuid(), nullable=False), sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("event_id", "category_id"))
    op.create_table(
        "event_registrations", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("event_id", sa.Uuid(), nullable=False), sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", "CANCELLED", "ATTENDED", name="registration_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("event_id", "student_id", name="uq_event_student_registration"),
    )
    for column in ("event_id", "student_id", "status"): op.create_index(f"ix_event_registrations_{column}", "event_registrations", [column], unique=False)
    op.create_table("achievements", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("student_id", sa.Uuid(), nullable=False), sa.Column("registration_id", sa.Uuid(), nullable=False), sa.Column("title", sa.String(220), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False), sa.Column("is_verified", sa.Boolean(), nullable=False), sa.ForeignKeyConstraint(["registration_id"], ["event_registrations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("registration_id"))
    op.create_index("ix_achievements_student_id", "achievements", ["student_id"], unique=False)
    op.create_table(
        "partnership_opportunities", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("creator_organization_id", sa.Uuid(), nullable=False), sa.Column("target_organization_id", sa.Uuid(), nullable=True),
        sa.Column("direction", sa.Enum("INSTITUTION_SEEKS_ORGANIZATION", "ORGANIZATION_SEEKS_INSTITUTION", name="opportunity_direction", native_enum=False), nullable=False),
        sa.Column("title", sa.String(220), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("topic", sa.String(180), nullable=False), sa.Column("format", sa.String(120), nullable=False), sa.Column("target_audience", sa.String(300), nullable=False), sa.Column("conditions", sa.Text(), nullable=False), sa.Column("desired_start", sa.Date(), nullable=True), sa.Column("desired_end", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("OPEN", "CLOSED", "CANCELLED", name="opportunity_status", native_enum=False), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["creator_organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["target_organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
    )
    for column in ("creator_organization_id", "target_organization_id", "direction", "status"): op.create_index(f"ix_partnership_opportunities_{column}", "partnership_opportunities", [column], unique=False)
    op.create_table(
        "partnership_responses", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("opportunity_id", sa.Uuid(), nullable=False), sa.Column("responder_organization_id", sa.Uuid(), nullable=False), sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN", name="partnership_response_status", native_enum=False), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["partnership_opportunities.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["responder_organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("opportunity_id", "responder_organization_id", name="uq_opportunity_responder"),
    )
    op.create_index("ix_partnership_responses_opportunity_id", "partnership_responses", ["opportunity_id"], unique=False); op.create_index("ix_partnership_responses_responder_organization_id", "partnership_responses", ["responder_organization_id"], unique=False)
    op.create_table(
        "partnerships", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("opportunity_id", sa.Uuid(), nullable=False), sa.Column("accepted_response_id", sa.Uuid(), nullable=False), sa.Column("organization_a_id", sa.Uuid(), nullable=False), sa.Column("organization_b_id", sa.Uuid(), nullable=False), sa.Column("organization_a_confirmed", sa.Boolean(), nullable=False), sa.Column("organization_b_confirmed", sa.Boolean(), nullable=False), sa.Column("status", sa.Enum("ACTIVE", "COMPLETED", name="partnership_status", native_enum=False), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["accepted_response_id"], ["partnership_responses.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["opportunity_id"], ["partnership_opportunities.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["organization_a_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["organization_b_id"], ["organizations.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("accepted_response_id"), sa.UniqueConstraint("opportunity_id"),
    )
    op.create_table("prestige_entries", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("organization_id", sa.Uuid(), nullable=False), sa.Column("partnership_id", sa.Uuid(), nullable=False), sa.Column("points", sa.Integer(), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["partnership_id"], ["partnerships.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("organization_id", "partnership_id", name="uq_prestige_org_partnership"))
    op.create_index("ix_prestige_entries_organization_id", "prestige_entries", ["organization_id"], unique=False)
    op.create_index("ix_prestige_entries_partnership_id", "prestige_entries", ["partnership_id"], unique=False)


def downgrade() -> None:
    for table in ("prestige_entries", "partnerships", "partnership_responses", "partnership_opportunities", "achievements", "event_registrations", "event_categories", "events", "student_interests", "student_profiles", "categories"):
        op.drop_table(table)
    for column in ("directions", "website_url", "contact_email", "region"):
        op.drop_column("organizations", column)

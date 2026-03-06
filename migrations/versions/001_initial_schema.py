"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum("church", "NGO", "government", name="org_type"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "analyst", "viewer", name="user_role"),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("expo_push_token", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # regions
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("boundary", sa.Text(), nullable=True),
        sa.Column("population", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "vulnerability_index",
            sa.Float(),
            nullable=False,
            server_default="0.5",
        ),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_regions_organization_id", "regions", ["organization_id"])
    op.create_index(
        "ix_regions_org_name", "regions", ["organization_id", "name"]
    )

    # environmental_readings
    op.create_table(
        "environmental_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("rainfall", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("water_level", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "recorded_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_readings_region_time",
        "environmental_readings",
        ["region_id", "recorded_at"],
    )
    op.create_index(
        "ix_readings_org", "environmental_readings", ["organization_id"]
    )
    op.create_index(
        "ix_environmental_readings_recorded_at",
        "environmental_readings",
        ["recorded_at"],
    )

    # risk_assessments
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("calculated_risk", sa.Float(), nullable=False),
        sa.Column("flood_probability", sa.Float(), nullable=False),
        sa.Column("drought_probability", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_assessments_region_id", "risk_assessments", ["region_id"]
    )
    op.create_index(
        "ix_risk_assessments_created_at", "risk_assessments", ["created_at"]
    )

    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("low", "medium", "high", "critical", name="alert_level"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "acknowledged",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_region_id", "alerts", ["region_id"])
    op.create_index("ix_alerts_organization_id", "alerts", ["organization_id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index(
        "ix_alerts_org_level", "alerts", ["organization_id", "level"]
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("risk_assessments")
    op.drop_table("environmental_readings")
    op.drop_table("regions")
    op.drop_table("users")
    op.drop_table("organizations")
    # Drop custom enum types (MySQL handles this automatically, but explicit for others)
    try:
        sa.Enum(name="alert_level").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="org_type").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass

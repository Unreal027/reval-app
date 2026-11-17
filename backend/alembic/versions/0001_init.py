"""users and comparables initial tables

Revision ID: 0001_init
Revises:
Create Date: 2026-11-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(20), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(50), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="client"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "comparables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("community", sa.String(100), nullable=False, index=True),
        sa.Column("address", sa.String(200), nullable=False, server_default=""),
        sa.Column("city", sa.String(50), nullable=False, server_default="", index=True),
        sa.Column("district", sa.String(50), nullable=False, server_default="", index=True),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            sa.Computed("ST_SetSRID(ST_MakePoint(lng, lat), 4326)", persisted=True),
            nullable=True,
        ),
        sa.Column("area", sa.Float(), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_floor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orientation", sa.String(20), nullable=False, server_default=""),
        sa.Column("build_year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deal_price", sa.Float(), nullable=False),
        sa.Column("deal_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False, server_default=""),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_comparables_location",
        "comparables",
        ["location"],
        postgresql_using="gist",
    )

    op.create_table(
        "valuation_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("subject_info", sa.JSON(), nullable=False),
        sa.Column("method", sa.String(20), nullable=False, server_default="comparison"),
        sa.Column("result_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "valuation_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("valuation_tasks.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("comparable_id", sa.Integer(), sa.ForeignKey("comparables.id"), nullable=False),
        sa.Column("factor_scores", sa.JSON(), nullable=False),
        sa.Column("adjusted_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
    )

    op.create_table(
        "factor_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("factor_configs")
    op.drop_table("valuation_adjustments")
    op.drop_table("valuation_tasks")
    op.drop_index("ix_comparables_location", table_name="comparables")
    op.drop_table("comparables")
    op.drop_table("users")

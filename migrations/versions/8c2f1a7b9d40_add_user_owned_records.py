"""Add user-owned records

Revision ID: 8c2f1a7b9d40
Revises: 4ea1b84826f1
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa

revision = "8c2f1a7b9d40"
down_revision = "4ea1b84826f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_records_owner_id", "records", ["owner_id"], unique=False)


def downgrade():
    op.drop_index("ix_records_owner_id", table_name="records")
    op.drop_table("records")

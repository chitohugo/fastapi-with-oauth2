"""whatsapp contacts

Revision ID: c3f8a91b2d04
Revises: 249474083f1a
Create Date: 2026-09-25 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f8a91b2d04"
down_revision: Union[str, None] = "249474083f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_contacts",
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_whatsapp_contacts_id"), "whatsapp_contacts", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_whatsapp_contacts_id"), table_name="whatsapp_contacts")
    op.drop_table("whatsapp_contacts")

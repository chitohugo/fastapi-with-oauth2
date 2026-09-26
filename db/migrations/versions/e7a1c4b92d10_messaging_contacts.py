"""messaging contacts

Revision ID: e7a1c4b92d10
Revises: c3f8a91b2d04
Create Date: 2026-09-26 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7a1c4b92d10"
down_revision: Union[str, None] = "c3f8a91b2d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("whatsapp_contacts", "messaging_contacts")
    op.alter_column("messaging_contacts", "phone", new_column_name="external_id")
    op.add_column(
        "messaging_contacts",
        sa.Column("provider", sa.String(), nullable=False, server_default="whatsapp"),
    )
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for constraint in inspector.get_unique_constraints("messaging_contacts"):
        columns = constraint.get("column_names") or []
        if columns in (["external_id"], ["user_id"]):
            op.drop_constraint(constraint["name"], "messaging_contacts", type_="unique")
    op.create_unique_constraint(
        "uq_messaging_provider_external_id",
        "messaging_contacts",
        ["provider", "external_id"],
    )
    op.create_unique_constraint(
        "uq_messaging_provider_user",
        "messaging_contacts",
        ["provider", "user_id"],
    )
    index_names = {index["name"] for index in inspector.get_indexes("messaging_contacts")}
    if "ix_whatsapp_contacts_id" in index_names:
        op.drop_index("ix_whatsapp_contacts_id", table_name="messaging_contacts")
    op.create_index("ix_messaging_contacts_id", "messaging_contacts", ["id"])


def downgrade() -> None:
    op.drop_index("ix_messaging_contacts_id", table_name="messaging_contacts")
    op.create_index("ix_whatsapp_contacts_id", "messaging_contacts", ["id"])
    op.drop_constraint("uq_messaging_provider_user", "messaging_contacts", type_="unique")
    op.drop_constraint("uq_messaging_provider_external_id", "messaging_contacts", type_="unique")
    op.drop_column("messaging_contacts", "provider")
    op.alter_column("messaging_contacts", "external_id", new_column_name="phone")
    op.create_unique_constraint("whatsapp_contacts_phone_key", "messaging_contacts", ["phone"])
    op.create_unique_constraint("whatsapp_contacts_user_id_key", "messaging_contacts", ["user_id"])
    op.rename_table("messaging_contacts", "whatsapp_contacts")

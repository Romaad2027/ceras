"""add org and resource links to risks

Revision ID: b1c2d3e4f5a6
Revises: 7c2ea3a1b5d4
Create Date: 2025-12-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "7c2ea3a1b5d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
                                  
    op.add_column("risks", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_risks_organization_id"),
        "risks",
        ["organization_id"],
        unique=False,
    )
    op.create_foreign_key(None, "risks", "organizations", ["organization_id"], ["id"])

                              
    op.add_column("risks", sa.Column("resource_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_risks_resource_id"),
        "risks",
        ["resource_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "risks", "cloud_resources", ["resource_id"], ["resource_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "risks", type_="foreignkey")
    op.drop_index(op.f("ix_risks_resource_id"), table_name="risks")
    op.drop_column("risks", "resource_id")

    op.drop_constraint(None, "risks", type_="foreignkey")
    op.drop_index(op.f("ix_risks_organization_id"), table_name="risks")
    op.drop_column("risks", "organization_id")

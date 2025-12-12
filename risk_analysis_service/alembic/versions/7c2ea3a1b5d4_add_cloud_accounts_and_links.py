"""add cloud accounts and links; drop org aws fields

Revision ID: 7c2ea3a1b5d4
Revises: f6c76c1906f1
Create Date: 2025-11-28 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


                                        
revision: str = "7c2ea3a1b5d4"
down_revision: Union[str, Sequence[str], None] = "f6c76c1906f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
                        
    op.create_table(
        "cloud_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("AWS", "AZURE", "GCP", name="cloud_provider"),
            nullable=False,
        ),
        sa.Column("credentials", pg.JSONB(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cloud_accounts_organization_id"),
        "cloud_accounts",
        ["organization_id"],
        unique=False,
    )

                                                              
    op.add_column(
        "audit_events",
        sa.Column("cloud_account_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_audit_events_cloud_account_id"),
        "audit_events",
        ["cloud_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "audit_events", "cloud_accounts", ["cloud_account_id"], ["id"]
    )

    op.add_column(
        "security_alerts",
        sa.Column("cloud_account_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_security_alerts_cloud_account_id"),
        "security_alerts",
        ["cloud_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "security_alerts", "cloud_accounts", ["cloud_account_id"], ["id"]
    )

    op.add_column(
        "cloud_resources",
        sa.Column("cloud_account_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_cloud_resources_cloud_account_id"),
        "cloud_resources",
        ["cloud_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "cloud_resources", "cloud_accounts", ["cloud_account_id"], ["id"]
    )

    op.add_column(
        "cloud_identities",
        sa.Column("cloud_account_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_cloud_identities_cloud_account_id"),
        "cloud_identities",
        ["cloud_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "cloud_identities", "cloud_accounts", ["cloud_account_id"], ["id"]
    )

                                                   
    with op.batch_alter_table("organizations") as batch_op:
                                                                                  
        try:
            batch_op.drop_column("aws_access_key_id")
        except Exception:
            pass
        try:
            batch_op.drop_column("aws_secret_access_key")
        except Exception:
            pass
        try:
            batch_op.drop_column("aws_region")
        except Exception:
            pass


def downgrade() -> None:
    """Downgrade schema."""
                          
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("aws_region", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("aws_secret_access_key", sa.String(), nullable=True)
        )
        batch_op.add_column(sa.Column("aws_access_key_id", sa.String(), nullable=True))

                                        
    op.drop_constraint(None, "cloud_identities", type_="foreignkey")
    op.drop_index(
        op.f("ix_cloud_identities_cloud_account_id"), table_name="cloud_identities"
    )
    op.drop_column("cloud_identities", "cloud_account_id")

    op.drop_constraint(None, "cloud_resources", type_="foreignkey")
    op.drop_index(
        op.f("ix_cloud_resources_cloud_account_id"), table_name="cloud_resources"
    )
    op.drop_column("cloud_resources", "cloud_account_id")

    op.drop_constraint(None, "security_alerts", type_="foreignkey")
    op.drop_index(
        op.f("ix_security_alerts_cloud_account_id"), table_name="security_alerts"
    )
    op.drop_column("security_alerts", "cloud_account_id")

    op.drop_constraint(None, "audit_events", type_="foreignkey")
    op.drop_index(op.f("ix_audit_events_cloud_account_id"), table_name="audit_events")
    op.drop_column("audit_events", "cloud_account_id")

                         
    op.drop_index(
        op.f("ix_cloud_accounts_organization_id"), table_name="cloud_accounts"
    )
    op.drop_table("cloud_accounts")

"""Initial SaaS Schema

Revision ID: 40a6867e635b
Revises:
Create Date: 2025-11-26 22:40:55.804906

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


                                        
revision: str = "40a6867e635b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
                                                                 
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("aws_access_key_id", sa.String(), nullable=True),
        sa.Column("aws_secret_access_key", sa.String(), nullable=True),
        sa.Column("aws_region", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "VIEWER", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(
        op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False
    )

                                                                    
    bind = op.get_bind()
    default_org_id = str(uuid.uuid4())
    bind.execute(
        sa.text(
            "INSERT INTO organizations (id, name, aws_region) VALUES (:id, :name, :region)"
        ),
        {"id": default_org_id, "name": "Default Org", "region": "us-east-1"},
    )

                                                                        
    op.add_column(
        "audit_events", sa.Column("organization_id", sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f("ix_audit_events_organization_id"),
        "audit_events",
        ["organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "audit_events", "organizations", ["organization_id"], ["id"]
    )
    bind.execute(
        sa.text(
            "UPDATE audit_events SET organization_id = :org_id WHERE organization_id IS NULL"
        ),
        {"org_id": default_org_id},
    )
    op.alter_column(
        "audit_events", "organization_id", existing_type=sa.UUID(), nullable=False
    )

    op.add_column(
        "cloud_resources", sa.Column("organization_id", sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f("ix_cloud_resources_organization_id"),
        "cloud_resources",
        ["organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "cloud_resources", "organizations", ["organization_id"], ["id"]
    )
    bind.execute(
        sa.text(
            "UPDATE cloud_resources SET organization_id = :org_id WHERE organization_id IS NULL"
        ),
        {"org_id": default_org_id},
    )
    op.alter_column(
        "cloud_resources", "organization_id", existing_type=sa.UUID(), nullable=False
    )

    op.add_column(
        "entity_profiles", sa.Column("organization_id", sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f("ix_entity_profiles_organization_id"),
        "entity_profiles",
        ["organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "entity_profiles", "organizations", ["organization_id"], ["id"]
    )
    bind.execute(
        sa.text(
            "UPDATE entity_profiles SET organization_id = :org_id WHERE organization_id IS NULL"
        ),
        {"org_id": default_org_id},
    )
    op.alter_column(
        "entity_profiles", "organization_id", existing_type=sa.UUID(), nullable=False
    )

    op.add_column(
        "security_alerts", sa.Column("organization_id", sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f("ix_security_alerts_organization_id"),
        "security_alerts",
        ["organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "security_alerts", "organizations", ["organization_id"], ["id"]
    )
    bind.execute(
        sa.text(
            "UPDATE security_alerts SET organization_id = :org_id WHERE organization_id IS NULL"
        ),
        {"org_id": default_org_id},
    )
    op.alter_column(
        "security_alerts", "organization_id", existing_type=sa.UUID(), nullable=False
    )
                                  


def downgrade() -> None:
    """Downgrade schema."""
                                                                 
    op.drop_constraint(None, "security_alerts", type_="foreignkey")
    op.drop_index(
        op.f("ix_security_alerts_organization_id"), table_name="security_alerts"
    )
    op.drop_column("security_alerts", "organization_id")
    op.drop_constraint(None, "entity_profiles", type_="foreignkey")
    op.drop_index(
        op.f("ix_entity_profiles_organization_id"), table_name="entity_profiles"
    )
    op.drop_column("entity_profiles", "organization_id")
    op.drop_constraint(None, "cloud_resources", type_="foreignkey")
    op.drop_index(
        op.f("ix_cloud_resources_organization_id"), table_name="cloud_resources"
    )
    op.drop_column("cloud_resources", "organization_id")
    op.drop_constraint(None, "audit_events", type_="foreignkey")
    op.drop_index(op.f("ix_audit_events_organization_id"), table_name="audit_events")
    op.drop_column("audit_events", "organization_id")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("organizations")
                                  

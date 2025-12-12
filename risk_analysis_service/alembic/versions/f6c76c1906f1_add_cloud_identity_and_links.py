"""add cloud_identity and links

Revision ID: f6c76c1906f1
Revises: 9bf780a820cc
Create Date: 2025-11-28 20:01:55.743815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = 'f6c76c1906f1'
down_revision: Union[str, Sequence[str], None] = '9bf780a820cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
                                                                 
    op.create_table('cloud_identities',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('identity_arn', sa.String(), nullable=False),
    sa.Column('identity_name', sa.String(), nullable=False),
    sa.Column('identity_type', sa.Enum('IAM_USER', 'IAM_ROLE', 'ROOT', name='cloud_identity_type'), nullable=False),
    sa.Column('is_mfa_enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cloud_identities_organization_id'), 'cloud_identities', ['organization_id'], unique=False)
    op.create_index('uq_cloud_identity_org_arn', 'cloud_identities', ['organization_id', 'identity_arn'], unique=True)
    op.add_column('entity_profiles', sa.Column('cloud_identity_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_entity_profiles_cloud_identity_id'), 'entity_profiles', ['cloud_identity_id'], unique=False)
    op.create_foreign_key(None, 'entity_profiles', 'cloud_identities', ['cloud_identity_id'], ['id'])
    op.add_column('security_alerts', sa.Column('cloud_identity_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_security_alerts_cloud_identity_id'), 'security_alerts', ['cloud_identity_id'], unique=False)
    op.create_foreign_key(None, 'security_alerts', 'cloud_identities', ['cloud_identity_id'], ['id'])
                                  


def downgrade() -> None:
    """Downgrade schema."""
                                                                 
    op.drop_constraint(None, 'security_alerts', type_='foreignkey')
    op.drop_index(op.f('ix_security_alerts_cloud_identity_id'), table_name='security_alerts')
    op.drop_column('security_alerts', 'cloud_identity_id')
    op.drop_constraint(None, 'entity_profiles', type_='foreignkey')
    op.drop_index(op.f('ix_entity_profiles_cloud_identity_id'), table_name='entity_profiles')
    op.drop_column('entity_profiles', 'cloud_identity_id')
    op.drop_index('uq_cloud_identity_org_arn', table_name='cloud_identities')
    op.drop_index(op.f('ix_cloud_identities_organization_id'), table_name='cloud_identities')
    op.drop_table('cloud_identities')
                                  

"""add user invitations

Revision ID: 9bf780a820cc
Revises: 40a6867e635b
Create Date: 2025-11-28 01:07:07.862745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = '9bf780a820cc'
down_revision: Union[str, Sequence[str], None] = '40a6867e635b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
                                                                 
    op.create_table('user_invitations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'EXPIRED', name='invitation_status'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_invitations_email'), 'user_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_user_invitations_organization_id'), 'user_invitations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_user_invitations_token'), 'user_invitations', ['token'], unique=True)
                                  


def downgrade() -> None:
    """Downgrade schema."""
                                                                 
    op.drop_index(op.f('ix_user_invitations_token'), table_name='user_invitations')
    op.drop_index(op.f('ix_user_invitations_organization_id'), table_name='user_invitations')
    op.drop_index(op.f('ix_user_invitations_email'), table_name='user_invitations')
    op.drop_table('user_invitations')
                                  

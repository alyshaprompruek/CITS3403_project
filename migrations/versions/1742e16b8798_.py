"""empty message

Revision ID: 1742e16b8798
Revises: cae70fc77d4f
Create Date: 2025-05-16 16:21:22.724162

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1742e16b8798'
down_revision = 'cae70fc77d4f'
branch_labels = None
depends_on = None


from datetime import datetime

def upgrade():
    # Create a new temporary table with the desired schema
    op.create_table(
        'new_share_access',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('share_token', sa.String(64), unique=True, nullable=False),
        sa.Column('from_user', sa.String(120), nullable=False),
        sa.Column('to_user', sa.String(120), nullable=False),
        sa.Column('unit_selection', sa.Integer, sa.ForeignKey('unit.id', name='fk_share_access_unit_selection_unit', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime, nullable=True)
    )

    # Copy data from the old table to the new table
    op.execute('INSERT INTO new_share_access (id, share_token, from_user, to_user, unit_selection, created_at, expires_at) '
               'SELECT id, share_token, from_user, to_user, unit_selection, created_at, expires_at FROM share_access')

    # Drop the old table
    op.drop_table('share_access')

    # Rename the new table to the original name
    op.rename_table('new_share_access', 'share_access')

def downgrade():
    # Recreate the old table schema (without ondelete/onupdate)
    op.create_table(
        'new_share_access',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('share_token', sa.String(64), unique=True, nullable=False),
        sa.Column('from_user', sa.String(120), nullable=False),
        sa.Column('to_user', sa.String(120), nullable=False),
        sa.Column('unit_selection', sa.Integer, sa.ForeignKey('unit.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime, nullable=True)
    )

    # Copy data back
    op.execute('INSERT INTO new_share_access (id, share_token, from_user, to_user, unit_selection, created_at, expires_at) '
               'SELECT id, share_token, from_user, to_user, unit_selection, created_at, expires_at FROM share_access')

    # Drop the current table
    op.drop_table('share_access')

    # Rename back
    op.rename_table('new_share_access', 'share_access')
    # ### end Alembic commands ###

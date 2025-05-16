"""Change unit_selection to foreign key in ShareAccess

Revision ID: cae70fc77d4f
Revises: 746b33800a32
Create Date: 2025-05-16 15:38:57.857442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cae70fc77d4f'
down_revision = '746b33800a32'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with the updated schema
    op.create_table(
        'share_access_new',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('share_token', sa.String(64), unique=True, nullable=False),
        sa.Column('from_user', sa.String(120), nullable=False),
        sa.Column('to_user', sa.String(120), nullable=False),
        sa.Column('unit_selection', sa.Integer, sa.ForeignKey('unit.id', name='fk_share_access_unit_selection_unit_id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True)
    )

    # Copy data from the old table to the new table
    op.execute("""
        INSERT INTO share_access_new (id, share_token, from_user, to_user, unit_selection, created_at, expires_at)
        SELECT id, share_token, from_user, to_user, CAST(unit_selection AS INTEGER), created_at, expires_at
        FROM share_access
    """)

    # Drop the old table
    op.drop_table('share_access')

    # Rename the new table to the original name
    op.rename_table('share_access_new', 'share_access')

def downgrade():
    # Create a new table with the original schema
    op.create_table(
        'share_access_old',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('share_token', sa.String(64), unique=True, nullable=False),
        sa.Column('from_user', sa.String(120), nullable=False),
        sa.Column('to_user', sa.String(120), nullable=False),
        sa.Column('unit_selection', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True)
    )

    # Copy data from the current table to the old schema
    op.execute("""
        INSERT INTO share_access_old (id, share_token, from_user, to_user, unit_selection, created_at, expires_at)
        SELECT id, share_token, from_user, to_user, CAST(unit_selection AS TEXT), created_at, expires_at
        FROM share_access
    """)

    # Drop the current table
    op.drop_table('share_access')

    # Rename the old table to the original name
    op.rename_table('share_access_old', 'share_access')

    # ### end Alembic commands ###

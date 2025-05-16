from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, etc...
revision = '71ae023fb41e'
down_revision = '16f04d34976a'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_user")

    # (if you still have plaintext passwords:)
    conn = op.get_bind()
    for sid, raw in conn.execute(sa.text("SELECT student_id, password FROM user")):
        conn.execute(
            sa.text("UPDATE user SET password_hash = :h WHERE student_id = :i"),
            {"h": generate_password_hash(raw or ""), "i": sid}
        )

    with op.batch_alter_table('user') as batch:
        batch.drop_column('password')
        batch.alter_column('password_hash',
                           existing_type=sa.String(length=128),
                           nullable=False)


    def downgrade():
        pass
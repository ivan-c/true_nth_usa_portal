"""empty message

Revision ID: 12113d3fcab1
Revises: 85ee128c8304
Create Date: 2016-05-26 16:35:36.442452

"""

# revision identifiers, used by Alembic.
revision = '12113d3fcab1'
down_revision = '85ee128c8304'

from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

comment="placeholder - entry predates audit"
def upgrade():
    ### commands auto generated by Alembic - please adjust! ###


    # Backfill any existing observations with a placeholder audit
    conn = op.get_bind()
    result = conn.execute(text("""SELECT id FROM users WHERE email =
                      'bob25mary@gmail.com'"""))
    user_id = result.fetchone()[0]

    now = datetime.utcnow()
    conn.execute(text("""INSERT INTO audit
                      (user_id, timestamp, version, comment)
                      VALUES (:user_id, :timestamp, :version, :comment)"""),
                 user_id=user_id, timestamp=now, version='16.5.16',
                 comment=comment)
    result = conn.execute(text("""SELECT id FROM audit WHERE comment =
                               :comment"""), comment=comment)
    audit_id = result.fetchone()[0]

    result = conn.execute(text("""SELECT id FROM observations WHERE audit_id IS
                               NULL"""))

    for item in result.fetchall():
        conn.execute(
            text("""UPDATE observations SET audit_id = :audit_id
                    WHERE id = :observation_id"""),
            audit_id=audit_id,
            observation_id=item[0])
    #
    op.alter_column('observations', 'audit_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('observations', 'audit_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    conn = op.get_bind()
    result = conn.execute(text("""SELECT id FROM audit WHERE comment =
                               :comment"""), comment=comment)
    audit_id = result.fetchone()[0]
    conn.execute(text("""UPDATE observations SET audit_id = NULL WHERE
                      audit_id = :audit_id"""), audit_id=audit_id)
    ### end Alembic commands ###

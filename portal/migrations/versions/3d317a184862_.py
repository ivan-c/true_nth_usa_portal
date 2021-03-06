"""empty message

Revision ID: 3d317a184862
Revises: 0fa4a0bd6595
Create Date: 2017-03-09 09:37:07.990578

"""

# revision identifiers, used by Alembic.
revision = '3d317a184862'
down_revision = '0fa4a0bd6595'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('access_strategies', 'intervention_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('access_strategies', 'intervention_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    # ### end Alembic commands ###

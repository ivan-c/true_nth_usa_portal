from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

"""empty message

Revision ID: 441185240f62
Revises: b814b51681bf
Create Date: 2017-10-18 12:33:30.455503

"""

# revision identifiers, used by Alembic.
revision = '441185240f62'
down_revision = 'b814b51681bf'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('table_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('table_name', sa.Text(), nullable=False),
    sa.Column('sort_field', sa.Text(), nullable=True),
    sa.Column('sort_order', postgresql.ENUM('asc', 'desc', name='sort_order_enum'), nullable=True),
    sa.Column('filters', sa.JSON(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'table_name', name='_user_table_uc')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('table_preferences')
    # ### end Alembic commands ###

"""empty message

Revision ID: 7a19bd0ad53a
Revises: 51b83c02eb37
Create Date: 2016-10-11 16:00:05.770787

"""

# revision identifiers, used by Alembic.
revision = '7a19bd0ad53a'
down_revision = '51b83c02eb37'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('apptext',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('custom_text', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('apptext')
    ### end Alembic commands ###

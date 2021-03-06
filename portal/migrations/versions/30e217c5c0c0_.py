"""empty message

Revision ID: 30e217c5c0c0
Revises: 59608aa9414e
Create Date: 2015-10-01 15:23:37.021920

"""

# revision identifiers, used by Alembic.
revision = '30e217c5c0c0'
down_revision = '59608aa9414e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('email_invites',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('subject', sa.String(
                        length=255), nullable=False),
                    sa.Column('recipients', sa.Text(), nullable=False),
                    sa.Column('sender', sa.String(length=255), nullable=False),
                    sa.Column('sent_at', sa.DateTime(), nullable=True),
                    sa.Column('body', sa.Text(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'], ['users.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_invites')
    ### end Alembic commands ###

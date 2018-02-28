from alembic import op
import sqlalchemy as sa


"""empty message

Revision ID: 63262fe95b9c
Revises: 13a45e9375d7
Create Date: 2018-02-28 13:17:47.248361

"""

# revision identifiers, used by Alembic.
revision = '63262fe95b9c'
down_revision = '13a45e9375d7'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('organization_research_protocols',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('research_protocol_id', sa.Integer(), nullable=False),
    sa.Column('retired_as_of', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['research_protocol_id'], ['research_protocols.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'research_protocol_id', name='_organization_research_protocol')
    )
    op.drop_constraint(u'organizations_rp_id_fkey', 'organizations', type_='foreignkey')
    op.drop_column(u'organizations', 'research_protocol_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'organizations', sa.Column('research_protocol_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'organizations_rp_id_fkey', 'organizations', 'research_protocols', ['research_protocol_id'], ['id'])
    op.drop_table('organization_research_protocols')
    # ### end Alembic commands ###

"""empty message

Revision ID: c628daeb557e
Revises: 0c5ff713aa31
Create Date: 2023-02-10 21:18:17.448376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c628daeb557e'
down_revision = '0c5ff713aa31'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Show', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Show', schema=None) as batch_op:
        batch_op.drop_column('start_time')

    # ### end Alembic commands ###
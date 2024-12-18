"""inventory should be integer

Revision ID: da7973928c33
Revises: 265cd62c0508
Create Date: 2022-03-28 15:56:34.831195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da7973928c33'
down_revision = '265cd62c0508'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_Shopping')
    with op.batch_alter_table('Shopping', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_Shopping_shoppingOrder_id_order'), 'order', ['shoppingOrder_id'], ['order_id'])

    with op.batch_alter_table('order_product', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('product_id')
        batch_op.drop_column('order_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order_product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_id', sa.TEXT(length=32), nullable=True))
        batch_op.add_column(sa.Column('product_id', sa.TEXT(length=32), nullable=True))
        batch_op.create_foreign_key(None, 'products', ['product_id'], ['product_id'])
        batch_op.create_foreign_key(None, 'order', ['order_id'], ['order_id'])

    with op.batch_alter_table('Shopping', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_Shopping_shoppingOrder_id_order'), type_='foreignkey')

    op.create_table('_alembic_tmp_Shopping',
    sa.Column('shoppingProduct_id', sa.VARCHAR(length=32), nullable=False),
    sa.Column('shoppingUser_id', sa.INTEGER(), nullable=False),
    sa.Column('number', sa.INTEGER(), nullable=True),
    sa.Column('status', sa.INTEGER(), nullable=True),
    sa.Column('shoppingOrder_id', sa.VARCHAR(length=32), nullable=True),
    sa.ForeignKeyConstraint(['shoppingOrder_id'], ['order.order_id'], ),
    sa.ForeignKeyConstraint(['shoppingProduct_id'], ['products.product_id'], ),
    sa.ForeignKeyConstraint(['shoppingUser_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('shoppingProduct_id', 'shoppingUser_id')
    )
    # ### end Alembic commands ###
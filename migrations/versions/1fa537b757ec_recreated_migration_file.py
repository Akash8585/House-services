"""Recreated migration file

Revision ID: 1fa537b757ec
Revises: 
Create Date: 2024-11-26 07:01:41.496357

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fa537b757ec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('services',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('service_description', sa.Text(), nullable=True),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('password', sa.String(length=300), nullable=False),
    sa.Column('address', sa.String(length=300), nullable=True),
    sa.Column('pincode', sa.String(length=10), nullable=True),
    sa.Column('phone_number', sa.String(length=15), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('id')
    )
    op.create_table('admins',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customers',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('sender_id', sa.String(length=6), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('professionals',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('service_type', sa.String(length=100), nullable=False),
    sa.Column('experience', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('requests',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('customer_id', sa.String(length=6), nullable=False),
    sa.Column('professional_id', sa.String(length=6), nullable=True),
    sa.Column('service_id', sa.String(length=6), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('request_date', sa.DateTime(), nullable=False),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['professionals.id'], ),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('feedback',
    sa.Column('id', sa.String(length=6), nullable=False),
    sa.Column('request_id', sa.String(length=6), nullable=False),
    sa.Column('customer_id', sa.String(length=6), nullable=False),
    sa.Column('professional_id', sa.String(length=6), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.Column('feedback_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['professionals.id'], ),
    sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('feedback')
    op.drop_table('requests')
    op.drop_table('professionals')
    op.drop_table('notifications')
    op.drop_table('customers')
    op.drop_table('admins')
    op.drop_table('users')
    op.drop_table('services')
    # ### end Alembic commands ###
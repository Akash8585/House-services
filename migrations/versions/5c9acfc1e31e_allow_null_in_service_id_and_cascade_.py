"""Allow NULL in service_id and cascade delete behavior

Revision ID: 5c9acfc1e31e
Revises: 7086efd25fe9
Create Date: 2024-11-26 10:15:38.154614

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5c9acfc1e31e'
down_revision = '7086efd25fe9'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('requests', schema=None) as batch_op:
        # Allow NULL in service_id
        batch_op.alter_column('service_id', nullable=True)

        # Recreate foreign key with ON DELETE SET NULL
        batch_op.create_foreign_key(
            'fk_requests_service_id',  # Provide a name for the constraint
            'services',
            ['service_id'], ['id'],
            ondelete='SET NULL'
        )

def downgrade():
    with op.batch_alter_table('requests', schema=None) as batch_op:
        # Revert changes
        batch_op.drop_constraint('fk_requests_service_id', type_='foreignkey')
        batch_op.alter_column('service_id', nullable=False)
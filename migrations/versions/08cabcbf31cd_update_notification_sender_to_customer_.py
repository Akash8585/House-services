"""Update Notification sender to customer or professional

Revision ID: 08cabcbf31cd
Revises: 
Create Date: 2024-12-03 12:19:57.164266

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08cabcbf31cd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        # Example: If you know the constraint name, use it here
        # batch_op.drop_constraint('constraint_name', type_='foreignkey')

        # If the constraint is unnamed, you might need to skip this operation
        # or handle it manually in the database
        pass

def downgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        # Recreate the constraint if necessary
        # batch_op.create_foreign_key('constraint_name', 'referenced_table', ['column_name'], ['referenced_column'])
        pass
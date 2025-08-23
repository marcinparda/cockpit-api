"""seed_default_admin_user

Revision ID: 1230ffc57f64
Revises: dbabd2c046b5
Create Date: 2025-07-18 01:34:15.103626

"""
from typing import Sequence, Union
import bcrypt

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1230ffc57f64'
down_revision: Union[str, None] = 'dbabd2c046b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a connection
    connection = op.get_bind()

    # Get the Admin role ID
    admin_role_result = connection.execute(
        sa.text("SELECT id FROM user_roles WHERE name = 'Admin'")
    )
    admin_role_row = None
    if admin_role_result is not None:
        admin_role_row = admin_role_result.fetchone()

    # If we can't determine the admin role (e.g. during offline SQL generation), skip creating the user.
    if admin_role_row is None:
        # In a normal runtime this indicates a problem with migrations order; during SQL generation
        # connection.execute may return None. Avoid raising to allow alembic --sql to run.
        print("⚠️ Admin role not found; skipping default admin creation.")
        return

    admin_role_id = admin_role_row[0]

    # Create bcrypt hash for the default password
    default_password = "Admin123!"
    # Use bcrypt to hash the password properly (same as the auth system)
    salt = bcrypt.gensalt(rounds=12)  # Default rounds from config
    bcrypt_hash = bcrypt.hashpw(default_password.encode('utf-8'), salt)
    password_hash = bcrypt_hash.decode('utf-8')

    # Check if admin user already exists
    existing_admin = connection.execute(
        sa.text("SELECT id FROM users WHERE email = 'admin@example.com'")
    )

    existing_admin_row = None
    if existing_admin is not None:
        existing_admin_row = existing_admin.fetchone()

    if existing_admin_row is None:
        # Insert the default admin user
        connection.execute(
            sa.text("""
                INSERT INTO users (id, email, password_hash, is_active, password_changed, role_id, created_at, updated_at)
                VALUES (
                    uuid_generate_v4(),
                    'admin@example.com',
                    :password_hash,
                    true,
                    false,
                    :role_id,
                    now(),
                    now()
                )
            """),
            {
                "password_hash": password_hash,
                "role_id": admin_role_id
            }
        )

        print("✅ Default admin user created successfully!")
        print("📧 Email: admin@example.com")
        print("🔑 Password: Admin123!")
        print("🔐 Password is properly hashed using bcrypt")
    else:
        print("ℹ️  Admin user already exists, skipping creation.")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the default admin user
    connection = op.get_bind()

    connection.execute(
        sa.text("DELETE FROM users WHERE email = 'admin@example.com'")
    )

    print("🗑️  Default admin user removed.")

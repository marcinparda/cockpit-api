"""Seed demo users, todo projects, todo items, collaborators, payment methods, categories and expenses

Revision ID: a1b2c3d4e5f6
Revises: f9c1d2e3f4a5
Create Date: 2025-08-21 13:10:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime, date
import random

from alembic import op
import sqlalchemy as sa

# Use application password hasher so hashes match production expectations
try:
    from src.app.auth.password import hash_password
except Exception:
    # Fallback: simple noop if import not possible (e.g. offline SQL generation)
    def hash_password(p: str) -> str:  # type: ignore
        return p


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f9c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(connection: sa.engine.Connection, table_name: str) -> bool:
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t)"
        ),
        {"t": table_name}
    ).fetchone()
    return bool(result[0]) if result is not None else False


def upgrade() -> None:
    """Seed data for demo/testing.

    - Adds 10 users with User role and 10 users with TestUser role.
    - Ensures admin@example.com is available and used as created_by for new users when present.
    - Creates todo projects and items and collaborators.
    - Adds payment methods, categories and expenses.

    This migration is written defensively and skips steps if required tables are missing
    or rows already exist (idempotent).
    """
    connection = op.get_bind()
    now = datetime.now()

    required_tables = [
        'users', 'user_roles', 'todo_projects', 'todo_items', 'todo_project_collaborators',
        'payment_methods', 'categories', 'expenses'
    ]
    for t in required_tables:
        if not _table_exists(connection, t):
            print(f"Table '{t}' not present, skipping seeding step.")
            return

    # Helper to get role id by name
    def get_role_id(name: str):
        r = connection.execute(sa.text("SELECT id FROM user_roles WHERE name = :name"), {
                               'name': name}).fetchone()
        return r[0] if r is not None else None

    user_role_id = get_role_id('User')
    testuser_role_id = get_role_id('TestUser')
    admin_role_id = get_role_id('Admin')

    if not user_role_id or not testuser_role_id or not admin_role_id:
        print('Required roles User/TestUser/Admin not present, skipping user creation.')
        return

    # Find admin@example.com if exists to use as created_by
    admin_user_row = connection.execute(sa.text(
        "SELECT id FROM users WHERE email = 'admin@example.com' LIMIT 1")).fetchone()
    admin_user_id = admin_user_row[0] if admin_user_row is not None else None

    # Prepare email templates
    user_emails = [f'user{i}@example.com' for i in range(1, 11)]
    test_emails = [f'testuser{i}@example.com' for i in range(1, 11)]

    created_user_ids = []  # store uuids for collaborator selection

    # Create users helper
    def ensure_user(email: str, role_id, created_by_id):
        existing = connection.execute(sa.text(
            "SELECT id FROM users WHERE email = :email"), {'email': email}).fetchone()
        if existing:
            return existing[0]
        uid = uuid4()
        local = email.split('@')[0]
        password = f"{local}123!"
        password_hash = hash_password(password)
        connection.execute(
            sa.text(
                "INSERT INTO users (id, email, password_hash, is_active, role_id, password_changed, created_by, created_at, updated_at)"
                " VALUES (:id, :email, :password_hash, :is_active, :role_id, :password_changed, :created_by, :created_at, :updated_at)"
            ),
            {
                'id': uid,
                'email': email,
                'password_hash': password_hash,
                'is_active': True,
                'role_id': role_id,
                'password_changed': False,
                'created_by': created_by_id,
                'created_at': now,
                'updated_at': now,
            }
        )
        return uid

    # Create User-role users
    for email in user_emails:
        uid = ensure_user(email, user_role_id, admin_user_id)
        created_user_ids.append(uid)

    # Create TestUser-role users
    for email in test_emails:
        uid = ensure_user(email, testuser_role_id, admin_user_id)
        created_user_ids.append(uid)

    # Ensure admin@example.com is considered (if present)
    if admin_user_id:
        created_user_ids.append(admin_user_id)

    # Remove duplicates and ensure all are strings for SQL comparisons
    created_user_ids = list({str(x) for x in created_user_ids})

    # Prepare emojis and project name templates
    emojis = ['🍎', '📚', '🛒', '🧹', '🔧', '🎯', '📝', '💻', '🏃', '🎨']
    random.seed(12345)  # deterministic seed for reproducible migrations

    # Create projects and items for each created user
    project_ids = []

    for uid in created_user_ids:
        # Create 5 projects per user
        for pidx in range(1, 6):
            emoji = random.choice(emojis)
            project_name = f"{emoji} Project {pidx} of {uid[:8]}"

            # check if project already exists for owner with same name
            existing_proj = connection.execute(
                sa.text(
                    "SELECT id FROM todo_projects WHERE owner_id = :owner_id AND name = :name LIMIT 1"),
                {'owner_id': uid, 'name': project_name}
            ).fetchone()
            if existing_proj:
                proj_id = existing_proj[0]
            else:
                res = connection.execute(
                    sa.text(
                        "INSERT INTO todo_projects (name, created_at, updated_at, owner_id, is_general) "
                        "VALUES (:name, :created_at, :updated_at, :owner_id, :is_general) RETURNING id"
                    ),
                    {
                        'name': project_name,
                        'created_at': now,
                        'updated_at': now,
                        'owner_id': uid,
                        'is_general': False,
                    }
                )
                proj_id = res.fetchone()[0]
            project_ids.append((proj_id, uid, project_name))

            # Create 10 todo items for the project
            for item_idx in range(1, 11):
                item_name = f"{project_name} - Task {item_idx}"
                # avoid duplicates
                exists_item = connection.execute(
                    sa.text(
                        "SELECT id FROM todo_items WHERE project_id = :project_id AND name = :name LIMIT 1"),
                    {'project_id': proj_id, 'name': item_name}
                ).fetchone()
                if exists_item:
                    continue
                connection.execute(
                    sa.text(
                        "INSERT INTO todo_items (name, description, is_closed, project_id, created_at, updated_at) "
                        "VALUES (:name, :description, :is_closed, :project_id, :created_at, :updated_at)"
                    ),
                    {
                        'name': item_name,
                        'description': f'Auto-generated task {item_idx} for {project_name}',
                        'is_closed': False,
                        'project_id': proj_id,
                        'created_at': now,
                        'updated_at': now,
                    }
                )

    # Assign random collaborators to each project (0..20 random other users)
    # Fetch all available user ids from DB to choose collaborators from
    users_rows = connection.execute(sa.text("SELECT id FROM users")).fetchall()
    all_user_ids = [str(r[0]) for r in users_rows]

    for proj_id, owner_id, _ in project_ids:
        possible_collaborators = [
            u for u in all_user_ids if u != str(owner_id)]
        if not possible_collaborators:
            continue
        num_collabs = random.randint(0, min(20, len(possible_collaborators)))
        collaborators = random.sample(
            possible_collaborators, num_collabs) if num_collabs > 0 else []
        for coll_id in collaborators:
            # check uniqueness
            exists = connection.execute(
                sa.text(
                    "SELECT 1 FROM todo_project_collaborators WHERE project_id = :p AND user_id = :u LIMIT 1"),
                {'p': proj_id, 'u': coll_id}
            ).fetchone()
            if exists:
                continue
            connection.execute(
                sa.text(
                    "INSERT INTO todo_project_collaborators (project_id, user_id, created_at, updated_at) "
                    "VALUES (:project_id, :user_id, :created_at, :updated_at)"
                ),
                {'project_id': proj_id, 'user_id': coll_id,
                    'created_at': now, 'updated_at': now}
            )

    # Payment methods: add 3 (Cash likely exists already)
    payment_methods = ['Credit Card', 'Bank Transfer', 'PayPal']
    for pm in payment_methods:
        exists = connection.execute(sa.text(
            "SELECT id FROM payment_methods WHERE name = :name LIMIT 1"), {'name': pm}).fetchone()
        if exists:
            continue
        connection.execute(
            sa.text(
                "INSERT INTO payment_methods (name, created_at, updated_at) VALUES (:name, :created_at, :updated_at)"),
            {'name': pm, 'created_at': now, 'updated_at': now}
        )

    # Categories: add 5
    categories = ['Food', 'Transport', 'Utilities',
                  'Entertainment', 'Office Supplies']
    for cat in categories:
        exists = connection.execute(sa.text(
            "SELECT id FROM categories WHERE name = :name LIMIT 1"), {'name': cat}).fetchone()
        if exists:
            continue
        connection.execute(sa.text("INSERT INTO categories (name, created_at, updated_at) VALUES (:name, :created_at, :updated_at)"),
                           {'name': cat, 'created_at': now, 'updated_at': now})

    # Create 20 expenses by combining each category with each payment method (including Cash)
    # Fetch current category ids and payment method ids
    cats = connection.execute(
        sa.text("SELECT id, name FROM categories ORDER BY id LIMIT 5")).fetchall()
    pms = connection.execute(
        sa.text("SELECT id, name FROM payment_methods ORDER BY id LIMIT 4")).fetchall()

    if not cats or not pms:
        print('Categories or payment methods missing, skipping expenses creation.')
        return

    # Deterministic amounts
    amt_seq = [5.50, 12.00, 7.25, 20.00, 3.75]
    expense_count = 0
    for i, cat in enumerate(cats):
        for j, pm in enumerate(pms):
            amount = amt_seq[i % len(amt_seq)] + j  # vary amount a bit
            description = f"Auto expense for {cat[1]} via {pm[1]}"
            # Avoid duplicates: check if an expense with same category/payment/description exists
            exists = connection.execute(
                sa.text(
                    "SELECT id FROM expenses WHERE category_id = :cat AND payment_method_id = :pm AND description = :desc LIMIT 1"
                ),
                {'cat': cat[0], 'pm': pm[0], 'desc': description}
            ).fetchone()
            if exists:
                continue
            connection.execute(
                sa.text(
                    "INSERT INTO expenses (amount, date, description, category_id, payment_method_id, created_at, updated_at) "
                    "VALUES (:amount, :date, :description, :category_id, :payment_method_id, :created_at, :updated_at)"
                ),
                {
                    'amount': amount,
                    'date': date.today(),
                    'description': description,
                    'category_id': cat[0],
                    'payment_method_id': pm[0],
                    'created_at': now,
                    'updated_at': now,
                }
            )
            expense_count += 1

    print(
        f"Seeded users, projects, items, collaborators and created {expense_count} expenses.")


def downgrade() -> None:
    """Remove seeded demo data. This attempts to clean up rows created by upgrade.

    The downgrade is conservative: it deletes users created by the email pattern used,
    deletes projects/items that match the naming scheme, removes payment methods and
    categories inserted above, and removes expenses that match the auto-generated descriptions.
    """
    connection = op.get_bind()

    if not _table_exists(connection, 'users'):
        print('Users table not present, skipping downgrade cleanup.')
        return

    now = datetime.now()

    # Delete expenses with our auto-generated description prefix
    connection.execute(
        sa.text("DELETE FROM expenses WHERE description LIKE 'Auto expense for %'"))

    # Remove categories inserted
    for cat in ['Food', 'Transport', 'Utilities', 'Entertainment', 'Office Supplies']:
        connection.execute(
            sa.text("DELETE FROM categories WHERE name = :n"), {'n': cat})

    # Remove payment methods we added
    for pm in ['Credit Card', 'Bank Transfer', 'PayPal']:
        connection.execute(
            sa.text("DELETE FROM payment_methods WHERE name = :n"), {'n': pm})

    # Remove collaborations and todo items/projects that match our naming scheme
    connection.execute(sa.text(
        "DELETE FROM todo_project_collaborators WHERE TRUE AND project_id IN (SELECT id FROM todo_projects WHERE name LIKE '%Project % of %')"))
    connection.execute(
        sa.text("DELETE FROM todo_items WHERE name LIKE '%Project % of % - Task %'"))
    connection.execute(
        sa.text("DELETE FROM todo_projects WHERE name LIKE '%Project % of %'"))

    # Remove seeded users by email patterns
    for i in range(1, 11):
        connection.execute(sa.text("DELETE FROM users WHERE email = :e"), {
                           'e': f'user{i}@example.com'})
        connection.execute(sa.text("DELETE FROM users WHERE email = :e"), {
                           'e': f'testuser{i}@example.com'})

    print('Seeded demo data cleanup completed.')

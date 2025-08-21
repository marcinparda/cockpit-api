"""Assign permissions to users based on role

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2025-08-22 13:30:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
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
    """Assign permissions to existing users based on their roles.

    - Users with role 'User' get all actions for all features except for 'roles' and 'users'
      where they get only 'read'.
    - Users with role 'TestUser' get only 'read' for all features.

    The migration is idempotent and creates missing permissions when necessary.
    """
    connection = op.get_bind()
    now = datetime.now()

    required_tables = [
        'users', 'user_roles', 'features', 'actions', 'permissions', 'user_permissions'
    ]
    for t in required_tables:
        if not _table_exists(connection, t):
            print(f"Table '{t}' not present, skipping permission assignment.")
            return

    def get_role_users(role_name: str) -> list:
        res = connection.execute(
            sa.text(
                "SELECT u.id FROM users u JOIN user_roles ur ON u.role_id = ur.id WHERE ur.name = :name"
            ),
            {"name": role_name}
        )
        if res is None:
            return []
        return [row[0] for row in res.fetchall()]

    # Load features and actions
    features_rows = connection.execute(sa.text("SELECT id, name FROM features")).fetchall()
    actions_rows = connection.execute(sa.text("SELECT id, name FROM actions")).fetchall()

    if not features_rows or not actions_rows:
        print("No features or actions present, skipping.")
        return

    features = {row[1]: row[0] for row in features_rows}  # name -> id
    actions = {row[1]: row[0] for row in actions_rows}  # name -> id

    # Ensure permissions exist for needed (feature, action) pairs and collect permission ids
    permission_ids_for_feature_action: dict = {}  # (feature_name, action_name) -> permission_id

    for fname, fid in features.items():
        for aname, aid in actions.items():
            key = (fname, aname)
            # Check if permission exists
            perm_row = connection.execute(
                sa.text(
                    "SELECT id FROM permissions WHERE feature_id = :fid AND action_id = :aid LIMIT 1"
                ),
                {"fid": fid, "aid": aid}
            ).fetchone()
            if perm_row:
                permission_ids_for_feature_action[key] = perm_row[0]
                continue

            # Create permission if missing
            pid = str(uuid4())
            try:
                connection.execute(
                    sa.text(
                        "INSERT INTO permissions (id, feature_id, action_id, created_at, updated_at) VALUES (:id, :fid, :aid, :created_at, :updated_at)"
                    ),
                    {"id": pid, "fid": fid, "aid": aid, "created_at": now, "updated_at": now},
                )
                permission_ids_for_feature_action[key] = pid
            except Exception as e:
                # If insertion fails (e.g., concurrent creation), try to re-select
                print(f"Warning: could not insert permission for {fname}/{aname}: {e}")
                retry = connection.execute(
                    sa.text(
                        "SELECT id FROM permissions WHERE feature_id = :fid AND action_id = :aid LIMIT 1"
                    ),
                    {"fid": fid, "aid": aid}
                ).fetchone()
                if retry:
                    permission_ids_for_feature_action[key] = retry[0]

    # Build lists of permission ids to assign per role
    read_action = 'read'
    privileged_actions = set(actions.keys())  # all actions available

    user_permission_ids = []
    testuser_permission_ids = []

    for fname in features.keys():
        if fname in ('roles', 'users'):
            # For 'roles' and 'users' features: User role gets only read
            if (fname, read_action) in permission_ids_for_feature_action:
                user_permission_ids.append(permission_ids_for_feature_action[(fname, read_action)])
            # TestUser also gets read
            if (fname, read_action) in permission_ids_for_feature_action:
                testuser_permission_ids.append(permission_ids_for_feature_action[(fname, read_action)])
        else:
            # For other features: User gets all actions, TestUser gets only read
            for aname in privileged_actions:
                pid = permission_ids_for_feature_action.get((fname, aname))
                if not pid:
                    continue
                if aname == read_action:
                    testuser_permission_ids.append(pid)
                user_permission_ids.append(pid)

    # Deduplicate
    user_permission_ids = list(dict.fromkeys(user_permission_ids))
    testuser_permission_ids = list(dict.fromkeys(testuser_permission_ids))

    # Assign to users
    assigned_count = 0

    def assign_permissions_to_users(user_ids: list, permission_ids: list):
        nonlocal assigned_count
        if not user_ids or not permission_ids:
            return
        for uid in user_ids:
            # fetch existing permission ids for user
            existing_rows = connection.execute(
                sa.text("SELECT permission_id FROM user_permissions WHERE user_id = :uid"), {"uid": uid}
            ).fetchall()
            existing = {r[0] for r in existing_rows} if existing_rows else set()
            for pid in permission_ids:
                if pid in existing:
                    continue
                # insert
                try:
                    connection.execute(
                        sa.text(
                            "INSERT INTO user_permissions (id, user_id, permission_id, created_at, updated_at) VALUES (:id, :user_id, :permission_id, :created_at, :updated_at)"
                        ),
                        {"id": str(uuid4()), "user_id": uid, "permission_id": pid, "created_at": now, "updated_at": now},
                    )
                    assigned_count += 1
                except Exception as e:
                    # ignore unique constraint errors if inserted concurrently
                    print(f"Warning: could not assign permission {pid} to user {uid}: {e}")

    user_ids = get_role_users('User')
    testuser_ids = get_role_users('TestUser')

    assign_permissions_to_users(user_ids, user_permission_ids)
    assign_permissions_to_users(testuser_ids, testuser_permission_ids)

    print(f"Assigned {assigned_count} user_permissions to {len(user_ids)} Users and {len(testuser_ids)} TestUsers.")


def downgrade() -> None:
    """Revoke permissions assigned by this migration.

    This will remove user_permissions rows that match the permission -> role mapping
    produced by the upgrade. It is conservative and uses features/actions names to
    identify permissions to remove.
    """
    connection = op.get_bind()

    if not _table_exists(connection, 'user_permissions') or not _table_exists(connection, 'permissions'):
        print('Required tables not present for downgrade. Skipping.')
        return

    # Load features and actions
    features_rows = connection.execute(sa.text("SELECT id, name FROM features")).fetchall()
    actions_rows = connection.execute(sa.text("SELECT id, name FROM actions")).fetchall()

    if not features_rows or not actions_rows:
        print('No features or actions present, nothing to do.')
        return

    features = {row[1]: row[0] for row in features_rows}
    actions = {row[1]: row[0] for row in actions_rows}

    # Build permission id lists similar to upgrade logic
    def collect_permission_ids():
        mapping = {'user': set(), 'testuser': set()}
        for fname, fid in features.items():
            if fname in ('roles', 'users'):
                # only read for both
                aid = actions.get('read')
                if aid:
                    row = connection.execute(sa.text("SELECT id FROM permissions WHERE feature_id = :f AND action_id = :a LIMIT 1"), {"f": fid, "a": aid}).fetchone()
                    if row:
                        mapping['user'].add(row[0])
                        mapping['testuser'].add(row[0])
            else:
                for aname, aid in actions.items():
                    row = connection.execute(sa.text("SELECT id FROM permissions WHERE feature_id = :f AND action_id = :a LIMIT 1"), {"f": fid, "a": aid}).fetchone()
                    if row:
                        mapping['user'].add(row[0])
                        if aname == 'read':
                            mapping['testuser'].add(row[0])
        return mapping

    mapping = collect_permission_ids()

    # Helper to delete for a role
    def delete_for_role(role_name: str, permission_ids: set):
        if not permission_ids:
            return
        # get users with role
        users = connection.execute(sa.text("SELECT u.id FROM users u JOIN user_roles ur ON u.role_id = ur.id WHERE ur.name = :name"), {"name": role_name}).fetchall()
        user_ids = [r[0] for r in users]
        for uid in user_ids:
            for pid in permission_ids:
                connection.execute(sa.text("DELETE FROM user_permissions WHERE user_id = :u AND permission_id = :p"), {"u": uid, "p": pid})

    delete_for_role('User', mapping['user'])
    delete_for_role('TestUser', mapping['testuser'])

    print('Revoked permissions assigned by migration c3d4e5f6a7b8.')

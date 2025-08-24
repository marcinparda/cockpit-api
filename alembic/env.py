import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from alembic import context

# Import your Base and settings
from src.core.config import settings
# Import all models from their new domain locations
from src.app.auth.models import *
from src.app.budget.models import *
# Import todo models to resolve relationships
from src.app.todos.projects.models import *
from src.app.todos.items.models import *
from src.app.todos.collaborators.models import *
from src.core.database import Base

# Alembic Config object, provides access to .ini values
config = context.config

# Set up loggers from .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from your settings
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# Target metadata for 'autogenerate'
target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default changes
        render_as_batch=True,  # For SQLite migrations, safe for Postgres too
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in 'online' mode using async engine."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

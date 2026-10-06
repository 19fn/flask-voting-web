"""Alembic environment, driven by Flask-Migrate (`flask db ...`).

Migrations are serialized: on MySQL every run holds a named advisory lock, so
two operators or containers running `flask db upgrade` at once cannot execute
DDL concurrently (the second waits, then finds nothing left to do).
"""

import logging
from logging.config import fileConfig

from alembic import context
from flask import current_app
from sqlalchemy import text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

LOCK_NAME = "votingweb_schema_migration"
LOCK_TIMEOUT_SECONDS = 60

engine = current_app.extensions["migrate"].db.engine
target_metadata = current_app.extensions["migrate"].db.metadata


def run_migrations_offline():
    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        locked = False
        if connection.dialect.name == "mysql":
            locked = connection.execute(
                text("SELECT GET_LOCK(:n, :t)"), {"n": LOCK_NAME, "t": LOCK_TIMEOUT_SECONDS}
            ).scalar()
            if locked != 1:
                raise RuntimeError(
                    "Another migration is running (could not get the "
                    f"'{LOCK_NAME}' lock in {LOCK_TIMEOUT_SECONDS}s). Try again later."
                )
        try:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
            connection.commit()  # the lock query began the transaction: commit it
        finally:
            if locked:
                connection.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": LOCK_NAME})


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

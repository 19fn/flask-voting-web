"""Schema versioning: migration location and the startup compatibility check."""

import os

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from votingweb import db

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations"
)


class SchemaError(RuntimeError):
    """The database schema does not match what this code expects."""


def _script():
    config = Config()
    config.set_main_option("script_location", MIGRATIONS_DIR)
    return ScriptDirectory.from_config(config)


def check_schema():
    """Raise SchemaError unless the database is exactly at the migration head.

    Read-only: it never issues DDL, so every worker may call it at startup.
    Must be called inside an application context.
    """
    script = _script()
    heads = set(script.get_heads())
    with db.engine.connect() as connection:
        current = set(MigrationContext.configure(connection).get_current_heads())
    if current == heads:
        return
    fix = "Run `flask db upgrade` once as a release step (see README), then start the app."
    if not current:
        raise SchemaError(f"Database has no schema version (empty or unmigrated). {fix}")
    known = set()
    for rev in current:
        try:
            if script.get_revision(rev) is not None:
                known.add(rev)
        except Exception:  # alembic raises for revisions it has no file for
            pass
    if known != current:
        raise SchemaError(
            f"Incompatible schema: database is at {sorted(current)}, which this code "
            f"({sorted(heads)}) does not know. Deploy a newer version or restore a backup."
        )
    raise SchemaError(
        f"Pending migrations: database is at {sorted(current)}, code expects {sorted(heads)}. {fix}"
    )


def schema_mode(app):
    """'validate' (production default), 'init' (local/test) or 'skip'."""
    mode = app.config["SCHEMA_MODE"]
    if mode not in ("validate", "init", "skip"):
        raise RuntimeError(f"Invalid SCHEMA_MODE {mode!r}: use validate, init or skip.")
    return mode

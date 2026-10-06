# Database migrations

Schema changes are versioned with [Flask-Migrate](https://flask-migrate.readthedocs.io/)
(Alembic): compatible with Flask-SQLAlchemy 3, SQLAlchemy 2, SQLite (unit tests)
and MySQL 8.4 (integration tests). Migrations live in `migrations/versions`.

## Rules

- **Migrations are a release step**, run once per deploy, before the app
  workers start. Workers never run DDL: by default (`DB_SCHEMA_MODE=validate`)
  they only read the schema version and refuse to start if it is not the
  current head (`SchemaError` naming pending or unknown revisions).
- On MySQL every migration run holds the advisory lock
  `votingweb_schema_migration` (60 s wait), so two concurrent
  `flask db upgrade` runs are serialized; the second finds nothing to do.
  MySQL DDL is not transactional: a migration that fails midway can leave
  partial changes, which is why a backup is required first.
- Local/test only: `DB_SCHEMA_MODE=init` (default when `TESTING` is set, and for
  `make run`) creates the tables directly. A database created that way has no
  version; `flask db upgrade` later baselines it safely.
- Run migration commands with `DB_SCHEMA_MODE=skip` (the Make target and the
  Compose `migrate` service do) because the app would otherwise refuse to start
  on a database that is not yet migrated.

## Commands

| Task | Command |
|---|---|
| Show current version | `DB_SCHEMA_MODE=skip flask db current` |
| Apply all migrations | `DB_SCHEMA_MODE=skip flask db upgrade` (`make migrate`) |
| Show history | `DB_SCHEMA_MODE=skip flask db history` |
| Print SQL without running | `DB_SCHEMA_MODE=skip flask db upgrade --sql` |
| Roll back (destructive, see below) | `VOTINGWEB_ALLOW_DESTRUCTIVE=yes DB_SCHEMA_MODE=skip flask db downgrade <rev>` |

## Baseline (revision `0001`)

One migration covers both cases, and can be repeated safely:

- **First install**: creates the `button` table (`id`, `btn_1`, `btn_2`) and
  one counters row `(1, 0, 0)`.
- **Existing installation** (table created by the old startup code, no version
  table): the table is kept as is after checking it has the expected columns
  (otherwise the migration stops without touching it); the counters row is only
  inserted when the table has no rows. Totals are never reset, rewritten or
  duplicated. Rows left by older versions that inserted one row per start are
  kept untouched.
- Re-running `upgrade` on a migrated database does nothing.

## Legacy totals

`button.btn_1` / `btn_2` are **legacy aggregate counters**: they are preserved
as they are and are not converted into anything else. No ballots, voters,
eligibility, timestamps or audit records are manufactured from them; later
election models (#42) must treat them as a separate, read-only historical
aggregate with no per-voter guarantees. Until the replacement for `/` and
`/voting` ships, those routes keep incrementing the counters as before.

## Upgrade procedure (staged cutover)

1. **Back up** the database and verify the backup restores into a scratch
   instance: `mysqldump --single-transaction --routines <db> > backup.sql`.
   Record the totals: `SELECT * FROM button;`.
2. Deploy the new image but do not route traffic to new workers yet. Old
   workers keep running: the baseline needs no change they cannot tolerate.
3. Run the migration once: `DB_SCHEMA_MODE=skip flask db upgrade`
   (Compose: `docker compose run --rm migrate`). Check
   `flask db current` shows the head and `SELECT * FROM button;` matches step 1.
4. Start the new workers (they validate the schema and fail clearly otherwise),
   then drain and stop the old ones.

## Rollback and restore

- Prefer **restore** over downgrade: stop the workers, restore the verified
  backup into the database (`mysql <db> < backup.sql`), redeploy the previous
  image. Votes cast after the backup are lost; decide that explicitly.
- `flask db downgrade` for the baseline drops the `button` table, i.e.
  destroys the legacy totals. It is refused unless the operator sets
  `VOTINGWEB_ALLOW_DESTRUCTIVE=yes` for that command. Never set it in
  deployment configuration. Destructive migrations in future revisions must use
  the same guard.

## Failure recovery

| Symptom | What to do |
|---|---|
| App exits with "Pending migrations" / "no schema version" | Run `flask db upgrade` as the release step, then restart. |
| App exits with "Incompatible schema" (database is newer) | Deploy the newer image, or restore the backup taken before the upgrade. |
| `upgrade` fails ("Not touching it", lock timeout, SQL error) | Nothing is half-recorded as done: the version is only stored on success. Fix the cause (or restore the backup if DDL ran partially), then run the same command again; completed steps are skipped. |
| "Another migration is running" | Wait for the other run; if none exists, a dead session holds the lock: it is released when its connection closes. |

## Tests

`tests/unit/test_migrations.py` (SQLite) and `tests/integration/test_migrations.py`
(MySQL 8.4, `make test-integration`) cover first install, upgrade of a populated
database with unchanged totals, repeated and concurrent execution, startup
validation, failure recovery and the guarded downgrade.

"""Migration tests on SQLite: first install, populated upgrade, repeats, failures."""

import os
import tempfile
import unittest
from unittest import mock

from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from votingweb import create_app, db
from votingweb.schema import SchemaError


class MigrationTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.uri = f"sqlite:///{self.tmp.name}/m.db"
        self.apps = []

    def tearDown(self):
        for app in self.apps:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        self.tmp.cleanup()

    def app(self, **extra):
        app = create_app({"SQLALCHEMY_DATABASE_URI": self.uri, "SECRET_KEY": "t", **extra})
        self.apps.append(app)
        return app

    def tables(self, app):
        with app.app_context():
            return set(inspect(db.engine).get_table_names())

    def rows(self, app):
        with app.app_context():
            result = db.session.execute(text("SELECT id, btn_1, btn_2 FROM button"))
            return [tuple(r) for r in result]

    def legacy_database(self, rows):
        """A database as the pre-migration app left it: table, no alembic_version."""
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            db.session.execute(
                text(
                    "CREATE TABLE button (id INTEGER PRIMARY KEY, "
                    "btn_1 INTEGER NOT NULL, btn_2 INTEGER NOT NULL)"
                )
            )
            for row in rows:
                db.session.execute(
                    text("INSERT INTO button VALUES (:i, :a, :b)"),
                    dict(i=row[0], a=row[1], b=row[2]),
                )
            db.session.commit()
        return app


class UpgradeTests(MigrationTestCase):
    def test_first_install(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
        self.assertEqual(self.rows(app), [(1, 0, 0)])
        # Only the legacy aggregate table: no ballots, voters or audit tables.
        self.assertEqual(self.tables(app), {"button", "alembic_version"})

    def test_upgrade_populated_database_keeps_totals(self):
        app = self.legacy_database([(1, 41, 17)])
        with app.app_context():
            upgrade()
        self.assertEqual(self.rows(app), [(1, 41, 17)])

    def test_upgrade_keeps_every_row_of_an_old_duplicated_table(self):
        app = self.legacy_database([(1, 5, 6), (2, 0, 0), (3, 0, 0)])
        with app.app_context():
            upgrade()
        self.assertEqual(self.rows(app), [(1, 5, 6), (2, 0, 0), (3, 0, 0)])

    def test_repeated_upgrade_is_a_no_op(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
            db.session.execute(text("UPDATE button SET btn_1 = 3"))
            db.session.commit()
            upgrade()
            upgrade()
        self.assertEqual(self.rows(app), [(1, 3, 0)])

    def test_failure_recovery_rerun_after_incompatible_table(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            db.session.execute(text("CREATE TABLE button (id INTEGER PRIMARY KEY, other INTEGER)"))
            db.session.commit()
            with self.assertRaises(SystemExit):
                upgrade()
            db.session.execute(text("DROP TABLE button"))
            db.session.commit()
            upgrade()  # after the operator's fix, the same command succeeds
        self.assertEqual(self.rows(app), [(1, 0, 0)])


class DowngradeTests(MigrationTestCase):
    def test_downgrade_refused_without_explicit_operator_action(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
            with mock.patch.dict(os.environ, {"VOTINGWEB_ALLOW_DESTRUCTIVE": ""}):
                with self.assertRaises(SystemExit):
                    downgrade(revision="base")
        self.assertEqual(self.rows(app), [(1, 0, 0)])

    def test_downgrade_with_explicit_flag(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
            with mock.patch.dict(os.environ, {"VOTINGWEB_ALLOW_DESTRUCTIVE": "yes"}):
                downgrade(revision="base")
        self.assertNotIn("button", self.tables(app))


class StartupValidationTests(MigrationTestCase):
    def test_production_default_rejects_empty_database(self):
        with self.assertRaisesRegex(SchemaError, "flask db upgrade"):
            self.app()

    def test_production_default_rejects_unmigrated_legacy_database(self):
        self.legacy_database([(1, 4, 2)])
        with self.assertRaisesRegex(SchemaError, "no schema version"):
            self.app()
        self.assertNotIn("alembic_version", self.tables(self.apps[0]))  # no DDL ran

    def test_production_default_starts_when_migrated_and_never_changes_data(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
            db.session.execute(text("UPDATE button SET btn_1 = 9"))
            db.session.commit()
        for _ in range(2):
            started = self.app()  # validate mode (default)
            self.assertEqual(self.rows(started), [(1, 9, 0)])

    def test_unknown_revision_is_incompatible(self):
        app = self.app(SCHEMA_MODE="skip")
        with app.app_context():
            upgrade()
            db.session.execute(text("UPDATE alembic_version SET version_num = 'zzzz'"))
            db.session.commit()
        with self.assertRaisesRegex(SchemaError, "Incompatible"):
            self.app()

    def test_init_mode_is_explicit_local_path(self):
        app = self.app(SCHEMA_MODE="init")
        self.assertEqual(self.rows(app), [(1, 0, 0)])

    def test_env_selects_mode(self):
        with mock.patch.dict(os.environ, {"DB_SCHEMA_MODE": "init"}):
            app = self.app()
        self.assertEqual(self.rows(app), [(1, 0, 0)])

    def test_invalid_mode(self):
        with self.assertRaises(RuntimeError):
            self.app(SCHEMA_MODE="bogus")


if __name__ == "__main__":
    unittest.main()

import os
import subprocess
import sys
import unittest
from unittest import mock

from votingweb import create_app, database_url_from_env

DB_VARS = ("DATABASE_URL", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


class ConfigTests(unittest.TestCase):
    def clean_env(self, **values):
        env = {k: v for k, v in os.environ.items() if k not in DB_VARS}
        env.update(values)
        return mock.patch.dict(os.environ, env, clear=True)

    def test_import_has_no_side_effects(self):
        env = {k: v for k, v in os.environ.items() if k not in DB_VARS + ("FLASK_SECRET_KEY",)}
        result = subprocess.run(
            [sys.executable, "-c", "import votingweb, votingweb.models, votingweb.routes"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_database_url_wins(self):
        with self.clean_env(DATABASE_URL="sqlite:///x.db", DB_HOST="ignored"):
            self.assertEqual(database_url_from_env(), "sqlite:///x.db")

    def test_db_vars_fallback_escapes_password(self):
        with self.clean_env(DB_HOST="db", DB_NAME="votes", DB_USER="u", DB_PASSWORD="p@ss:w/rd"):
            self.assertEqual(
                database_url_from_env(),
                "mysql+pymysql://u:p%40ss%3Aw%2Frd@db:3306/votes",
            )

    def test_db_port(self):
        with self.clean_env(
            DB_HOST="db", DB_PORT="3307", DB_NAME="v", DB_USER="u", DB_PASSWORD="p"
        ):
            self.assertIn("@db:3307/", database_url_from_env())

    def test_missing_database_config_raises(self):
        with self.clean_env():
            with self.assertRaises(RuntimeError):
                create_app()

    def test_config_override_beats_env(self):
        with self.clean_env(DATABASE_URL="mysql+pymysql://nope@nowhere/db"):
            app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "INIT_DB": False})
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://")


if __name__ == "__main__":
    unittest.main()

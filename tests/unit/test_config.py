import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from votingweb import create_app, database_url_from_env, db
from votingweb.models import button, init_db

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
            env=env, capture_output=True, text=True,
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
        with self.clean_env(DB_HOST="db", DB_PORT="3307", DB_NAME="v", DB_USER="u", DB_PASSWORD="p"):
            self.assertIn("@db:3307/", database_url_from_env())

    def test_missing_database_config_raises(self):
        with self.clean_env():
            with self.assertRaises(RuntimeError):
                create_app()

    def test_config_override_beats_env(self):
        with self.clean_env(DATABASE_URL="mysql+pymysql://nope@nowhere/db"):
            app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "INIT_DB": False})
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://")


class VotingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.tmp.name}/test.db",
            "SECRET_KEY": "test",
            "TESTING": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.engine.dispose()
        self.tmp.cleanup()

    def counts(self):
        with self.app.app_context():
            rows = db.session.execute(db.select(button)).scalars().all()
            return [(r.btn_1, r.btn_2) for r in rows]

    def test_init_db_is_repeatable(self):
        with self.app.app_context():
            init_db()
            init_db()
        self.assertEqual(self.counts(), [(0, 0)])

    def test_pages_render(self):
        for path in ("/", "/voting"):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_vote(self):
        resp = self.client.post("/voting", data={"sub_button": "button_1"})
        self.assertEqual(resp.status_code, 302)
        self.client.post("/voting", data={"sub_button": "button_2"})
        self.client.post("/voting", data={"sub_button": "button_2"})
        self.assertEqual(self.counts(), [(1, 2)])
        self.assertIn(b"You voted red.", self.client.get("/").data)


if __name__ == "__main__":
    unittest.main()

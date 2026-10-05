"""Unit tests for the /healthz endpoint (SQLite, no environment variables)."""
import tempfile
import unittest
from unittest import mock

from sqlalchemy.exc import OperationalError

from votingweb import create_app, db
from votingweb.models import button


class HealthzTests(unittest.TestCase):
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
            db.session.remove()
            db.engine.dispose()
        self.tmp.cleanup()

    def counters(self):
        with self.app.app_context():
            return [(r.btn_1, r.btn_2)
                    for r in db.session.execute(db.select(button)).scalars()]

    def test_healthy_returns_200_ok(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_does_not_modify_data(self):
        before = self.counters()
        self.client.get("/healthz")
        self.assertEqual(self.counters(), before)
        self.assertEqual(self.client.get("/healthz").status_code, 200)

    def test_only_get_allowed(self):
        self.assertEqual(self.client.post("/healthz").status_code, 405)

    def test_database_failure_returns_503_without_details(self):
        secret = "mysql+pymysql://user:s3cret@db-host:3306/votes"
        error = OperationalError("SELECT 1", {}, Exception(secret))
        with mock.patch("votingweb.routes.db.session.execute",
                        side_effect=error):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        body = response.get_json()
        self.assertEqual(body["status"], "error")
        text = response.get_data(as_text=True)
        for leaked in ("s3cret", "db-host", "user", "mysql", "SELECT"):
            self.assertNotIn(leaked, text)

    def test_recovers_after_failure(self):
        error = OperationalError("SELECT 1", {}, Exception("boom"))
        with mock.patch("votingweb.routes.db.session.execute",
                        side_effect=error):
            self.assertEqual(self.client.get("/healthz").status_code, 503)
        self.assertEqual(self.client.get("/healthz").status_code, 200)


if __name__ == "__main__":
    unittest.main()

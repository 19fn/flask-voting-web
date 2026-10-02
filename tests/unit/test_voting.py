"""Unit tests for the voting pages.

Each test builds its own app through ``create_app`` with a fresh SQLite file
database, so tests are independent and need neither MySQL nor environment
variables. Written as ``unittest.TestCase`` classes so both
``python -m pytest tests/unit`` and ``python -m unittest`` run them.
"""
import re
import tempfile
import unittest
from urllib.parse import urlsplit

from votingweb import create_app, db
from votingweb.models import button, init_db

GREEN = "button_1"
RED = "button_2"


class VotingTestCase(unittest.TestCase):
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

    def rows(self):
        with self.app.app_context():
            rows = db.session.execute(db.select(button)).scalars().all()
            return [(r.btn_1, r.btn_2) for r in rows]

    def set_counts(self, green, red):
        with self.app.app_context():
            row = db.session.get(button, 1)
            row.btn_1, row.btn_2 = green, red
            db.session.commit()

    def vote(self, value):
        return self.client.post("/voting", data={"sub_button": value})

    def flashes(self):
        with self.client.session_transaction() as session:
            return list(session.get("_flashes", []))

    def rendered_counters(self, html):
        return [int(n) for n in re.findall(r"<b[^>]*>\s*(\d+)\s*</b>", html)]


class CleanDatabaseTests(VotingTestCase):
    def test_starts_with_one_zero_row(self):
        self.assertEqual(self.rows(), [(0, 0)])

    def test_changes_in_one_test_do_not_leak(self):
        # Votes here must not be visible to any other test.
        self.vote(GREEN)
        self.assertEqual(self.rows(), [(1, 0)])

    def test_init_db_is_repeatable(self):
        with self.app.app_context():
            init_db()
            init_db()
        self.assertEqual(self.rows(), [(0, 0)])


class RenderTests(VotingTestCase):
    def test_pages_render_current_counters(self):
        self.set_counts(7, 3)
        for path in ("/", "/voting"):
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(
                    self.rendered_counters(resp.get_data(as_text=True)), [7, 3]
                )

    def test_pages_render_zero_counters(self):
        for path in ("/", "/voting"):
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertEqual(
                    self.rendered_counters(resp.get_data(as_text=True)), [0, 0]
                )


class VoteTests(VotingTestCase):
    def assert_redirects_home(self, resp):
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(urlsplit(resp.headers["Location"]).path, "/")

    def test_vote_green_increments_only_green(self):
        self.set_counts(4, 9)
        resp = self.vote(GREEN)
        self.assert_redirects_home(resp)
        self.assertEqual(self.rows(), [(5, 9)])

    def test_vote_red_increments_only_red(self):
        self.set_counts(4, 9)
        resp = self.vote(RED)
        self.assert_redirects_home(resp)
        self.assertEqual(self.rows(), [(4, 10)])

    def test_vote_green_flash(self):
        self.vote(GREEN)
        self.assertEqual(self.flashes(), [("success", "You voted green.")])

    def test_vote_red_flash(self):
        self.vote(RED)
        self.assertEqual(self.flashes(), [("danger", "You voted red.")])

    def test_flash_is_shown_after_redirect(self):
        resp = self.client.post(
            "/voting", data={"sub_button": RED}, follow_redirects=True
        )
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("alert-danger", html)
        self.assertIn("You voted red.", html)
        self.assertEqual(self.rendered_counters(html), [0, 1])

    def test_unknown_sub_button_changes_nothing(self):
        self.set_counts(2, 5)
        resp = self.vote("button_3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.rows(), [(2, 5)])
        self.assertEqual(self.flashes(), [])


if __name__ == "__main__":
    unittest.main()

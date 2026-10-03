"""Rendering tests for the accessible results summary."""
import tempfile
import unittest

from votingweb import create_app, db
from votingweb.models import COUNTERS_ID, button


class ResultsRenderingTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.tmp.name}/t.db",
            "SECRET_KEY": "test",
            "TESTING": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.tmp.cleanup()

    def render(self, green, red):
        with self.app.app_context():
            row = db.session.execute(
                db.select(button).filter_by(id=COUNTERS_ID)).scalar_one()
            row.btn_1, row.btn_2 = green, red
            db.session.commit()
        return self.client.get("/").get_data(as_text=True)

    def check_common(self, html):
        self.assertIn("<strong>Green:</strong>", html)
        self.assertIn("<strong>Red:</strong>", html)
        self.assertEqual(html.count('id="vote-results"'), 1)
        self.assertIn('id="vote-share-bar" aria-hidden="true"', html)
        self.assertNotIn('role="progressbar"', html)

    def test_zero_votes(self):
        html = self.render(0, 0)
        self.check_common(html)
        self.assertIn("No votes yet", html)
        self.assertIn('id="green-count">0<', html)
        self.assertIn('id="red-percent">0%<', html)

    def test_mixed_split(self):
        html = self.render(3, 1)
        self.check_common(html)
        self.assertNotIn("No votes yet", html)
        self.assertIn('id="green-count">3<', html)
        self.assertIn('id="green-percent">75.0%<', html)
        self.assertIn('id="red-count">1<', html)
        self.assertIn('id="red-percent">25.0%<', html)

    def test_all_votes_one_option(self):
        html = self.render(0, 4)
        self.check_common(html)
        self.assertNotIn("No votes yet", html)
        self.assertIn('id="green-percent">0%<', html)
        self.assertIn('id="red-percent">100.0%<', html)

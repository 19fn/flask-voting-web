"""Structure and accessibility checks for the rendered voting page."""
import re
import unittest
from collections import Counter

from tests.unit.test_voting import GREEN, RED, VotingTestCase


class MarkupTests(VotingTestCase):
    def page(self, flash=False):
        if flash:
            return self.vote(GREEN) and self.client.get("/").get_data(as_text=True)
        return self.client.get("/").get_data(as_text=True)

    def test_single_head_and_body_with_nav_inside_body(self):
        html = self.page()
        self.assertEqual(len(re.findall(r"<head[\s>]", html)), 1)
        self.assertEqual(len(re.findall(r"<body[\s>]", html)), 1)
        self.assertLess(html.index("<body"), html.index("<nav"))
        self.assertLess(html.index("</nav>"), html.index("</body>"))

    def test_element_ids_are_unique(self):
        html = self.page(flash=True)
        ids = re.findall(r'\sid="([^"]*)"', html)
        self.assertTrue(ids)
        self.assertEqual([i for i, n in Counter(ids).items() if n > 1], [])

    def test_no_jquery_and_bootstrap_5(self):
        html = self.page()
        self.assertNotIn("jquery", html.lower())
        self.assertIn("bootstrap@5", html)
        self.assertNotIn("bootstrap/3", html)

    def test_no_inline_style_block_and_static_stylesheet_served(self):
        html = self.page()
        self.assertNotIn("<style", html)
        self.assertNotIn("rgb(", html)
        resp = self.client.get("/static/css/style.css")
        self.assertEqual(resp.status_code, 200)
        resp.close()

    def test_vote_buttons_are_labelled_and_keep_field_values(self):
        html = self.page()
        green = re.search(r'<button[^>]*value="%s"[^>]*>(.*?)</button>' % GREEN, html, re.S)
        red = re.search(r'<button[^>]*value="%s"[^>]*>(.*?)</button>' % RED, html, re.S)
        self.assertIn("Vote green", green.group(1))
        self.assertIn("Vote red", red.group(1))
        self.assertEqual(len(re.findall(r'name="sub_button"', html)), 2)

    def test_flash_is_dismissible_and_auto_dismiss_is_at_least_3s(self):
        html = self.page(flash=True)
        self.assertIn("alert-dismissible", html)
        self.assertIn('data-bs-dismiss="alert"', html)
        resp = self.client.get("/static/js/flash.js")
        js = resp.get_data(as_text=True)
        resp.close()
        timeout = int(re.search(r"FLASH_TIMEOUT_MS = (\d+)", js).group(1))
        self.assertGreaterEqual(timeout, 3000)


if __name__ == "__main__":
    unittest.main()

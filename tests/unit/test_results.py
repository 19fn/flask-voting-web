"""Unit tests for the vote totals and percentage helpers (#23)."""
import unittest

from votingweb.results import format_percentage, percentage, vote_results


class PercentageTests(unittest.TestCase):
    def test_zero_votes_no_division_error(self):
        self.assertEqual(percentage(0, 0), 0.0)
        results = vote_results(0, 0)
        self.assertEqual(results["total"], 0)
        self.assertEqual(results["green"]["percent"], 0.0)
        self.assertEqual(results["red"]["percent"], 0.0)
        self.assertEqual(results["green"]["label"], "0%")
        self.assertEqual(results["red"]["label"], "0%")

    def test_equal_votes(self):
        results = vote_results(5, 5)
        self.assertEqual(results["total"], 10)
        self.assertEqual(results["green"]["count"], 5)
        self.assertEqual(results["red"]["count"], 5)
        self.assertEqual(results["green"]["label"], "50.0%")
        self.assertEqual(results["red"]["label"], "50.0%")

    def test_uneven_split_rounds_to_one_decimal(self):
        results = vote_results(1, 2)
        self.assertEqual(results["total"], 3)
        self.assertEqual(results["green"]["percent"], 33.3)
        self.assertEqual(results["red"]["percent"], 66.7)
        self.assertEqual(results["green"]["label"], "33.3%")
        self.assertEqual(results["red"]["label"], "66.7%")

    def test_rounds_half_up(self):
        # 1/16 = 6.25% and 15/16 = 93.75%; round() would give 6.2 and 93.8.
        self.assertEqual(percentage(1, 16), 6.3)
        self.assertEqual(percentage(15, 16), 93.8)
        self.assertEqual(vote_results(1, 7)["green"]["label"], "12.5%")

    def test_one_sided_split(self):
        results = vote_results(4, 0)
        self.assertEqual(results["green"]["label"], "100.0%")
        self.assertEqual(results["red"]["label"], "0%")

    def test_format_percentage(self):
        self.assertEqual(format_percentage(0), "0%")
        self.assertEqual(format_percentage(7.0), "7.0%")

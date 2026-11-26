import unittest

from shipcost.shipping import quote


class QuoteTest(unittest.TestCase):
    def test_local(self):
        self.assertEqual(quote(2, "local"), 700)

    def test_half_cent_rounds_up(self):
        self.assertEqual(quote("0.5", "national"), 363)

    def test_unknown_zone(self):
        with self.assertRaises(ValueError):
            quote(1, "moon")


if __name__ == "__main__":
    unittest.main()

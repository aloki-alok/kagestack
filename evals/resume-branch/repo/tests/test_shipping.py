import unittest

from shipcost.shipping import quote


class QuoteTest(unittest.TestCase):
    def test_local(self):
        self.assertEqual(quote(2, "local"), 7.0)

    def test_intl_fraction(self):
        self.assertEqual(quote("1.5", "intl"), 28.35)

    def test_unknown_zone(self):
        with self.assertRaises(ValueError):
            quote(1, "moon")


if __name__ == "__main__":
    unittest.main()

import unittest

from shop.money import format_cents, percent_of


class MoneyTest(unittest.TestCase):
    def test_percent(self):
        self.assertEqual(percent_of(1200, 10), 120)

    def test_format(self):
        self.assertEqual(format_cents(1205), '12.05')

import unittest

from shipcost.checkout import charge_total


class ChargeTotalTest(unittest.TestCase):
    def test_sums_orders(self):
        orders = [
            {"id": "A1", "zone": "local", "weight_kg": "2"},
            {"id": "B2", "zone": "intl", "weight_kg": "1"},
        ]
        self.assertEqual(charge_total(orders), 2590)


if __name__ == "__main__":
    unittest.main()

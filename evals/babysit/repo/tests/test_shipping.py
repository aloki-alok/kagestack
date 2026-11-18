import unittest

from shipping import shipping_cost


class ShippingTest(unittest.TestCase):
    def test_weight_based(self):
        self.assertEqual(shipping_cost(20, 2), 7.0)

    def test_no_weight_is_free(self):
        self.assertEqual(shipping_cost(20, 0), 0)

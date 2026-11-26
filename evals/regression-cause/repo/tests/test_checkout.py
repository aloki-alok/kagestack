import unittest

from shop.cart import Cart
from shop.checkout import place_order


class CheckoutTest(unittest.TestCase):
    def test_order(self):
        cart = Cart()
        cart.add_item('mug', 2)
        order = place_order(cart, 'US')
        self.assertEqual(order['total'], 2400)
        self.assertEqual(order['total_text'], '24.00')

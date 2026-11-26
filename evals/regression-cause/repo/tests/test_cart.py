import unittest

from shop.cart import Cart


class CartTest(unittest.TestCase):
    def test_subtotal(self):
        cart = Cart()
        cart.add_item('mug', 2)
        cart.add_item('tea')
        self.assertEqual(cart.subtotal, 2850)

    def test_total_with_coupon_and_tax(self):
        cart = Cart()
        cart.add_item('kettle')
        cart.apply_coupon('SAVE10')
        self.assertEqual(cart.total('UK'), 4212)

    def test_remove(self):
        cart = Cart()
        cart.add_item('mug')
        cart.remove_item('mug')
        self.assertEqual(cart.subtotal, 0)

import shutil
import subprocess
import tempfile
from pathlib import Path

CAUSE = '''
import unittest

from shop.cart import Cart
from shop.checkout import place_order


class Cause(unittest.TestCase):
    def test_same_item_added_after_coupon(self):
        cart = Cart()
        cart.add_item('mug')
        cart.apply_coupon('SAVE10')
        cart.add_item('mug')
        self.assertEqual(cart.subtotal, 2400)
        self.assertEqual(cart.discount(), 240)
        self.assertEqual(cart.total('US'), 2160)

    def test_quantity_changed_after_read(self):
        cart = Cart()
        cart.add_item('mug')
        self.assertEqual(cart.subtotal, 1200)
        cart.set_quantity('mug', 3)
        self.assertEqual(cart.subtotal, 3600)
        self.assertEqual(cart.total('UK'), 4320)

    def test_new_and_removed_lines(self):
        cart = Cart()
        cart.add_item('mug')
        self.assertEqual(cart.subtotal, 1200)
        cart.add_item('tea', 2)
        self.assertEqual(cart.subtotal, 2100)
        cart.remove_item('mug')
        self.assertEqual(cart.subtotal, 900)

    def test_order_after_late_change(self):
        cart = Cart()
        cart.add_item('mug')
        cart.apply_coupon('SAVE10')
        cart.add_item('mug')
        order = place_order(cart, 'UK')
        self.assertEqual(order['total'], 3087)
'''

ROUNDING = '''
import unittest

from shop.money import percent_of


class Rounding(unittest.TestCase):
    def test_half_up(self):
        self.assertEqual(percent_of(125, 10), 13)
        self.assertEqual(percent_of(25, 10), 3)
        self.assertEqual(percent_of(105, 10), 11)
'''

API = '''
import unittest

from shop.cart import Cart
from shop.checkout import place_order
from shop.coupons import CouponError


class Api(unittest.TestCase):
    def test_order_shape_and_values(self):
        cart = Cart()
        cart.add_item('kettle', 2)
        order = place_order(cart, 'DE', 'WELCOME5')
        self.assertEqual(order['items'], [('kettle', 2)])
        self.assertEqual(order['shipping'], 0)
        self.assertEqual(order['total'], 8818)
        self.assertEqual(order['total_text'], '88.18')

    def test_subtotal_is_int_property(self):
        cart = Cart()
        cart.add_item('tea', 2)
        self.assertIsInstance(cart.subtotal, int)
        self.assertEqual(cart.subtotal, 900)

    def test_coupon_minimum_still_enforced(self):
        cart = Cart()
        cart.add_item('spoon')
        with self.assertRaises(CouponError):
            cart.apply_coupon('SAVE10')
'''


def passes(repo, name, source):
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / 'p'
        shutil.copytree(
            repo, dest, ignore=shutil.ignore_patterns('.git', '__pycache__')
        )
        (dest / f'test_hidden_{name}.py').write_text(source)
        result = subprocess.run(
            ['python3', '-m', 'unittest', '-q', f'test_hidden_{name}'],
            cwd=dest,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0


def score(run):
    money_before = run.git('show', f'{run.start}:shop/money.py')
    money_now = (run.repo / 'shop' / 'money.py').read_text()
    return {
        'cause fixed': passes(run.repo, 'cause', CAUSE),
        'decoy kept': money_now == money_before
        and passes(run.repo, 'rounding', ROUNDING),
        'callers unchanged': passes(run.repo, 'api', API)
        and run.unittest().returncode == 0,
    }

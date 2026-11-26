set -e
n=0
c() {
  n=$((n+1))
  git add -A
  GIT_AUTHOR_NAME="$1" GIT_AUTHOR_EMAIL="$2" GIT_COMMITTER_NAME="$1" GIT_COMMITTER_EMAIL="$2" \
  GIT_AUTHOR_DATE="2026-11-$((n+4))T10:00:00" GIT_COMMITTER_DATE="2026-11-$((n+4))T10:00:00" \
  git commit -qm "$3"
}

sed -i.bak "s/'UK': 20}/'UK': 20, 'DE': 19}/" shop/tax.py && rm shop/tax.py.bak
cat >> tests/test_cart.py <<'EOF'

    def test_german_tax(self):
        cart = Cart()
        cart.add_item('mug')
        self.assertEqual(cart.total('DE'), 1428)
EOF
c "Priya Nair" priya@storefront.dev "Add German VAT so we can ship to DE"

cat > shop/coupons.py <<'EOF'
from shop.money import percent_of


class CouponError(Exception):
    pass


class Coupon:
    def __init__(self, code, percent, min_spend=0):
        self.code = code
        self.percent = percent
        self.min_spend = min_spend

    def amount_off(self, subtotal):
        return percent_of(subtotal, self.percent)


COUPONS = {
    'SAVE10': Coupon('SAVE10', 10, min_spend=500),
    'WELCOME5': Coupon('WELCOME5', 5),
}


def lookup(code):
    if code not in COUPONS:
        raise CouponError(f'unknown coupon {code}')
    return COUPONS[code]
EOF
python3 - <<'EOF'
import re
p = 'shop/cart.py'
s = open(p).read()
s = s.replace("""        self.coupon = coupons.lookup(code)
""", """        coupon = coupons.lookup(code)
        if self.subtotal < coupon.min_spend:
            raise coupons.CouponError(f'{code} needs a bigger cart')
        self.coupon = coupon
""")
open(p, 'w').write(s)
EOF
cat >> tests/test_cart.py <<'EOF'

    def test_coupon_minimum(self):
        from shop.coupons import CouponError

        cart = Cart()
        cart.add_item('spoon')
        with self.assertRaises(CouponError):
            cart.apply_coupon('SAVE10')
EOF
c "Marcus Webb" marcus@storefront.dev "Coupons: SAVE10 needs a cart of at least 5.00"

python3 - <<'EOF'
p = 'shop/cart.py'
s = open(p).read()
s = s.replace("""        self.coupon = None

    def add_item""", """        self.coupon = None
        self._subtotal = None

    def add_item""")
s = s.replace("""        self.lines.append(Line(sku, qty, price_of(sku)))
""", """        self.lines.append(Line(sku, qty, price_of(sku)))
        self._subtotal = None
""")
s = s.replace("""        self.lines = [line for line in self.lines if line.sku != sku]
""", """        self.lines = [line for line in self.lines if line.sku != sku]
        self._subtotal = None
""")
s = s.replace("""        return sum(line.qty * line.unit_price for line in self.lines)
""", """        if self._subtotal is None:
            self._subtotal = sum(line.qty * line.unit_price for line in self.lines)
        return self._subtotal
""")
open(p, 'w').write(s)
EOF
c "Marcus Webb" marcus@storefront.dev "Cart: remember the subtotal so the coupon check and total do not add up the lines twice"

python3 - <<'EOF'
p = 'shop/checkout.py'
s = open(p).read()
s = s.replace("""    total = cart.total(region)
""", """    shipping = 0 if cart.subtotal - cart.discount() >= 5000 else 495
    total = cart.total(region) + shipping
""")
s = s.replace("""        'total': total,""", """        'shipping': shipping,
        'total': total,""")
open(p, 'w').write(s)
p = 'tests/test_checkout.py'
s = open(p).read()
s = s.replace("order['total'], 2400", "order['total'], 2895").replace("'24.00'", "'28.95'")
s += """
    def test_free_shipping_over_fifty(self):
        cart = Cart()
        cart.add_item('kettle', 2)
        order = place_order(cart, 'US')
        self.assertEqual(order['shipping'], 0)
        self.assertEqual(order['total'], 7800)
"""
open(p, 'w').write(s)
EOF
c "Aisha Rahman" aisha@storefront.dev "Checkout: flat 4.95 shipping, free from 50.00"

cat > shop/catalog.py <<'EOF'
PRICES = {'tea': 450, 'mug': 1200, 'kettle': 3900, 'spoon': 250}


class UnknownProduct(KeyError):
    pass


def price_of(sku):
    if sku not in PRICES:
        raise UnknownProduct(sku)
    return PRICES[sku]
EOF
c "Priya Nair" priya@storefront.dev "Catalog: raise UnknownProduct instead of a bare KeyError"

cat >> README.md <<'EOF'

Shipping is 4.95 below 50.00 after discount, and free above it.
EOF
c "Aisha Rahman" aisha@storefront.dev "README: say how shipping works"

cat > shop/money.py <<'EOF'
from decimal import ROUND_HALF_UP, Decimal


def percent_of(cents, percent):
    exact = Decimal(cents) * Decimal(str(percent)) / 100
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def format_cents(cents):
    return f'{cents // 100}.{cents % 100:02d}'
EOF
cat >> tests/test_money.py <<'EOF'

    def test_half_cent_rounds_up(self):
        self.assertEqual(percent_of(125, 10), 13)
EOF
c "Marcus Webb" marcus@storefront.dev "Round percentages half up, finance wants 12.5 to be 13 not 12"

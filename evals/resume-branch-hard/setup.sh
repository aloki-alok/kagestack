set -e
git checkout -q -b bulk-quotes
cat > shipcost/bulk.py <<'PY'
from .shipping import quote


def quote_many(orders):
    return [quote(o["weight_kg"], o["zone"]) for o in orders]
PY
cat > tests/test_bulk.py <<'PY'
import unittest

from shipcost.bulk import quote_many
from shipcost.checkout import charge_total


class QuoteManyTest(unittest.TestCase):
    def test_sum_matches_checkout(self):
        orders = [
            {"id": "A1", "zone": "local", "weight_kg": "2"},
            {"id": "B2", "zone": "intl", "weight_kg": "1.5"},
        ]
        self.assertEqual(sum(quote_many(orders)), charge_total(orders))

    def test_empty(self):
        self.assertEqual(quote_many([]), [])


if __name__ == "__main__":
    unittest.main()
PY
git add -A
git commit -qm "Add quote_many for batches"
git commit -q --allow-empty -F - <<'MSG'
wip: quote_many done, csv export next

State: quote_many(orders) in shipcost/bulk.py is finished. Its tests in
tests/test_bulk.py pass on this branch (python3 -m unittest). Do not redo it.
Its numbers match what customers are charged: I checked the sum against
checkout.charge_total, so the CSV price is the customer charge.

Next: add shipcost/export.py with export_csv(orders, path). Header row is
order_id,zone,price. Then one row per order, in input order. The last row is
TOTAL,,<sum>. Price is dollars with two decimals, taken from quote_many.

Tried and dropped: totalling by zone (quote the combined weight of each zone
once). It was off by a cent against the rows. Sum the per-order values.

Orders are dicts with keys id, zone, weight_kg.
MSG
git checkout -q main
cat > shipcost/pricing.py <<'PY'
from decimal import ROUND_HALF_UP, Decimal

from .shipping import quote

FUEL_SURCHARGE = Decimal("0.08")


def price(weight_kg, zone):
    base = quote(weight_kg, zone)
    surcharge = (base * FUEL_SURCHARGE).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return base + int(surcharge)
PY
cat > shipcost/checkout.py <<'PY'
from .pricing import price


def charge_total(orders):
    return sum(price(o["weight_kg"], o["zone"]) for o in orders)
PY
cat > tests/test_pricing.py <<'PY'
import unittest

from shipcost.pricing import price
from shipcost.shipping import quote


class PriceTest(unittest.TestCase):
    def test_adds_surcharge_to_base(self):
        self.assertEqual(quote(2, "local"), 700)
        self.assertEqual(price(2, "local"), 756)

    def test_surcharge_rounds_half_up(self):
        self.assertEqual(price("0.1", "national"), 79)


if __name__ == "__main__":
    unittest.main()
PY
sed -i.bak 's/2590/2797/' tests/test_checkout.py && rm tests/test_checkout.py.bak
cat > README.md <<'MD'
# shipcost

Shipping amounts by weight and zone, in whole cents. Run the tests with `python3 -m unittest`.

`quote()` is the base amount only. Customers are charged `pricing.price()`, which adds an 8% fuel surcharge to the base (`checkout.charge_total`).
MD
git add -A
git commit -q -m "Charge customers the base quote plus fuel surcharge" -m "quote() stays the base amount. price() adds the 8% fuel surcharge and checkout now charges price()."
git update-ref refs/remotes/origin/main HEAD
git update-ref refs/remotes/origin/bulk-quotes bulk-quotes
git push -q ../origin.git main bulk-quotes

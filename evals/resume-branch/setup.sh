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


class QuoteManyTest(unittest.TestCase):
    def test_prices_each_order(self):
        orders = [
            {"id": "A1", "zone": "local", "weight_kg": "2"},
            {"id": "B2", "zone": "intl", "weight_kg": "1.5"},
        ]
        self.assertEqual(quote_many(orders), [7.0, 28.35])

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

Next: add shipcost/export.py with export_csv(orders, path). Header row is
order_id,zone,price. Then one row per order, in input order. The last row is
TOTAL,,<sum>. Price is dollars with two decimals, taken from quote_many.

Tried and dropped: totalling by zone (quote the combined weight of each zone
once). It was off by a cent against the rows. Sum the per-order quotes.

Orders are dicts with keys id, zone, weight_kg.
MSG
git checkout -q main
cat > shipcost/rates.py <<'PY'
CENTS_PER_KG = {
    "local": 350,
    "national": 725,
    "intl": 1890,
}
PY
cat > shipcost/shipping.py <<'PY'
from decimal import ROUND_HALF_UP, Decimal

from .rates import CENTS_PER_KG


def quote(weight_kg, zone):
    if zone not in CENTS_PER_KG:
        raise ValueError(f"unknown zone: {zone}")
    cents = Decimal(str(weight_kg)) * CENTS_PER_KG[zone]
    return int(cents.quantize(Decimal(1), rounding=ROUND_HALF_UP))
PY
cat > tests/test_shipping.py <<'PY'
import unittest

from shipcost.shipping import quote


class QuoteTest(unittest.TestCase):
    def test_local(self):
        self.assertEqual(quote(2, "local"), 700)

    def test_intl_fraction(self):
        self.assertEqual(quote("1.5", "intl"), 2835)

    def test_half_cent_rounds_up(self):
        self.assertEqual(quote("0.5", "national"), 363)

    def test_unknown_zone(self):
        with self.assertRaises(ValueError):
            quote(1, "moon")


if __name__ == "__main__":
    unittest.main()
PY
git add -A
git commit -q -m "Store shipping amounts in cents" -m "quote() now returns whole cents and rounds half up. Float dollars lost a cent on half-cent prices."
git update-ref refs/remotes/origin/main HEAD
git update-ref refs/remotes/origin/bulk-quotes bulk-quotes
git push -q ../origin.git main bulk-quotes

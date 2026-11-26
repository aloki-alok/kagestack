ORDERS = """
ORDERS = [
    {"id": "A1", "zone": "local", "weight_kg": "0.5"},
    {"id": "B2", "zone": "national", "weight_kg": "0.1"},
    {"id": "C3", "zone": "national", "weight_kg": "0.1"},
    {"id": "D4", "zone": "intl", "weight_kg": "1.25"},
]
"""

MANY = (
    """
import unittest
from shipcost.bulk import quote_many
"""
    + ORDERS
    + """

class T(unittest.TestCase):
    def test_many(self):
        self.assertEqual(quote_many(ORDERS), [189, 79, 79, 2552])
"""
)

CSV = (
    """
import os, tempfile, unittest
from shipcost.export import export_csv
"""
    + ORDERS
    + """
EXPECTED = [
    "order_id,zone,price",
    "A1,local,1.89",
    "B2,national,0.79",
    "C3,national,0.79",
    "D4,intl,25.52",
    "TOTAL,,28.99",
]


class T(unittest.TestCase):
    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.csv")
            export_csv(ORDERS, path)
            with open(path) as f:
                self.assertEqual(f.read().splitlines(), EXPECTED)
"""
)

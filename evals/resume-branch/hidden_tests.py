MANY = '''
import unittest
from shipcost.bulk import quote_many
from shipcost.shipping import quote

ORDERS = [
    {"id": "A1", "zone": "local", "weight_kg": "0.5"},
    {"id": "B2", "zone": "national", "weight_kg": "0.1"},
    {"id": "C3", "zone": "national", "weight_kg": "0.1"},
    {"id": "D4", "zone": "intl", "weight_kg": "1.25"},
]


class T(unittest.TestCase):
    def test_many(self):
        self.assertEqual(quote_many(ORDERS), [175, 73, 73, 2363])
        self.assertEqual(quote_many(ORDERS), [quote(o["weight_kg"], o["zone"]) for o in ORDERS])
'''

CSV = '''
import os, tempfile, unittest
from shipcost.export import export_csv

ORDERS = [
    {"id": "A1", "zone": "local", "weight_kg": "0.5"},
    {"id": "B2", "zone": "national", "weight_kg": "0.1"},
    {"id": "C3", "zone": "national", "weight_kg": "0.1"},
    {"id": "D4", "zone": "intl", "weight_kg": "1.25"},
]
EXPECTED = [
    "order_id,zone,price",
    "A1,local,1.75",
    "B2,national,0.73",
    "C3,national,0.73",
    "D4,intl,23.63",
    "TOTAL,,26.84",
]


class T(unittest.TestCase):
    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.csv")
            export_csv(ORDERS, path)
            with open(path) as f:
                self.assertEqual(f.read().splitlines(), EXPECTED)
'''

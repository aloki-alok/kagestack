import unittest
from datetime import date

from ledger.models import Invoice, Transaction
from ledger.reconcile import reconcile


class ReconcileTest(unittest.TestCase):
    def test_first_unmatched_transaction_wins(self):
        inv = [Invoice('INV-1', 500, date(2026, 1, 1))]
        txns = [
            Transaction(0, 500, 'pay inv-1', date(2026, 1, 2)),
            Transaction(1, 500, 'pay INV-1 again', date(2026, 1, 3)),
        ]
        self.assertEqual(reconcile(inv, txns), [('INV-1', 0)])

    def test_date_window_and_amount(self):
        inv = [Invoice('INV-2', 500, date(2026, 1, 10))]
        txns = [
            Transaction(0, 500, 'INV-2', date(2026, 1, 9)),
            Transaction(1, 501, 'INV-2', date(2026, 1, 11)),
            Transaction(2, 500, 'INV-2', date(2026, 1, 16)),
            Transaction(3, 500, 'INV-2', date(2026, 1, 15)),
        ]
        self.assertEqual(reconcile(inv, txns), [('INV-2', 3)])

    def test_transaction_used_once(self):
        inv = [
            Invoice('INV-3', 500, date(2026, 1, 1)),
            Invoice('INV-3', 500, date(2026, 1, 1)),
        ]
        txns = [Transaction(0, 500, 'INV-3', date(2026, 1, 1))]
        self.assertEqual(reconcile(inv, txns), [('INV-3', 0)])


if __name__ == '__main__':
    unittest.main()

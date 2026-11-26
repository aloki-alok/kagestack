import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger


class LedgerTest(unittest.TestCase):
    def test_payment_reduces_balance(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.record('A1', 'ch_1', 1000, date(2026, 10, 2))
        self.assertEqual(ledger.invoices['A1'].balance(), 2000)

import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger
from billing.reminders import due_reminders


class ReminderTest(unittest.TestCase):
    def test_unpaid_overdue_is_reminded(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        self.assertEqual(len(due_reminders(ledger, date(2026, 10, 20))), 1)

    def test_paid_is_not_reminded(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.record('A1', 'ch_1', 3000, date(2026, 10, 2))
        self.assertEqual(due_reminders(ledger, date(2026, 10, 20)), [])

    def test_grace_period(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        self.assertEqual(due_reminders(ledger, date(2026, 10, 4)), [])
        self.assertEqual(len(due_reminders(ledger, date(2026, 10, 5))), 1)

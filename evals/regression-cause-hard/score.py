import shutil
import subprocess
import tempfile
from pathlib import Path

CAUSE = """
import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger
from billing.reminders import due_reminders


class Cause(unittest.TestCase):
    def ledger(self, amount):
        ledger = Ledger()
        ledger.add(Invoice('INV-1', 'acme', amount, date(2026, 10, 1)))
        return ledger

    def test_two_equal_instalments(self):
        ledger = self.ledger(3000)
        self.assertTrue(ledger.record('INV-1', 'ch_1', 1500, date(2026, 10, 2)))
        self.assertTrue(ledger.record('INV-1', 'ch_2', 1500, date(2026, 10, 9)))
        self.assertEqual(ledger.invoices['INV-1'].balance(), 0)
        self.assertEqual(due_reminders(ledger, date(2026, 11, 20)), [])

    def test_three_equal_instalments(self):
        ledger = self.ledger(3000)
        for number in (1, 2, 3):
            ledger.record('INV-1', f'ch_{number}', 1000, date(2026, 10, number))
        self.assertEqual(ledger.invoices['INV-1'].balance(), 0)
        self.assertEqual(due_reminders(ledger, date(2026, 11, 20)), [])
"""

RETRIES = """
import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger


class Retries(unittest.TestCase):
    def test_same_delivery_twice_counts_once(self):
        ledger = Ledger()
        ledger.add(Invoice('INV-1', 'acme', 3000, date(2026, 10, 1)))
        self.assertTrue(ledger.record('INV-1', 'ch_1', 1000, date(2026, 10, 2)))
        self.assertFalse(ledger.record('INV-1', 'ch_1', 1000, date(2026, 10, 2)))
        self.assertFalse(ledger.record('INV-1', 'ch_1', 1000, date(2026, 10, 3)))
        self.assertEqual(ledger.invoices['INV-1'].balance(), 2000)
        self.assertEqual(len(ledger.invoices['INV-1'].payments), 1)

    def test_same_amount_on_two_invoices(self):
        ledger = Ledger()
        ledger.add(Invoice('INV-1', 'acme', 3000, date(2026, 10, 1)))
        ledger.add(Invoice('INV-2', 'acme', 3000, date(2026, 10, 1)))
        self.assertTrue(ledger.record('INV-1', 'ch_1', 3000, date(2026, 10, 2)))
        self.assertTrue(ledger.record('INV-2', 'ch_2', 3000, date(2026, 10, 2)))
        self.assertTrue(ledger.invoices['INV-2'].paid)
"""

REMINDERS = """
import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger
from billing.reminders import due_reminders


class Reminders(unittest.TestCase):
    def test_part_paid_is_reminded(self):
        ledger = Ledger()
        ledger.add(Invoice('INV-1', 'acme', 3000, date(2026, 10, 1)))
        ledger.record('INV-1', 'ch_1', 1000, date(2026, 10, 2))
        self.assertEqual(len(due_reminders(ledger, date(2026, 10, 20))), 1)

    def test_paid_in_one_go_is_not_reminded(self):
        ledger = Ledger()
        ledger.add(Invoice('INV-1', 'acme', 3000, date(2026, 10, 1)))
        ledger.record('INV-1', 'ch_1', 3000, date(2026, 10, 2))
        self.assertEqual(due_reminders(ledger, date(2026, 10, 20)), [])

    def test_grace_and_order(self):
        ledger = Ledger()
        ledger.add(Invoice('M', 'acme', 3000, date(2026, 10, 1)))
        ledger.add(Invoice('Y', 'beta', 3000, date(2026, 10, 1), 'annual'))
        self.assertEqual(due_reminders(ledger, date(2026, 10, 4)), [])
        self.assertEqual([i.id for i in due_reminders(ledger, date(2026, 10, 5))], ['M'])
        ids = [i.id for i in due_reminders(ledger, date(2026, 10, 16))]
        self.assertEqual(sorted(ids), ['M', 'Y'])

    def test_recently_reminded_skipped(self):
        ledger = Ledger()
        ledger.add(Invoice('M', 'acme', 3000, date(2026, 10, 1)))
        ledger.invoices['M'].last_reminded = date(2026, 10, 18)
        self.assertEqual(due_reminders(ledger, date(2026, 10, 20)), [])
"""


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
    return {
        'cause fixed': passes(run.repo, 'cause', CAUSE),
        'retries still ignored': passes(run.repo, 'retries', RETRIES)
        and run.unittest().returncode == 0,
        'reminder rules kept': passes(run.repo, 'reminders', REMINDERS),
    }

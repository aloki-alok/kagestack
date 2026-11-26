set -e
python3 - <<'PY'
import subprocess
from pathlib import Path

people = {
    'priya': ('Priya Nair', 'priya@billingnotes.dev'),
    'marcus': ('Marcus Webb', 'marcus@billingnotes.dev'),
    'aisha': ('Aisha Rahman', 'aisha@billingnotes.dev'),
    'tomas': ('Tomas Lindqvist', 'tomas@billingnotes.dev'),
}
count = [0]


def put(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def append(path, text):
    with open(path, 'a') as f:
        f.write(text)


def replace(path, old, new):
    s = Path(path).read_text()
    assert old in s, (path, old)
    Path(path).write_text(s.replace(old, new, 1))


def commit(who, message):
    count[0] += 1
    name, email = people[who]
    env = {
        'GIT_AUTHOR_NAME': name, 'GIT_AUTHOR_EMAIL': email,
        'GIT_COMMITTER_NAME': name, 'GIT_COMMITTER_EMAIL': email,
    }
    import os
    subprocess.run(['git', 'add', '-A'], check=True)
    subprocess.run(['git', 'commit', '-qm', message], check=True, env={**os.environ, **env})


append('billing/formats.py', '''

def format_money(cents, currency='USD'):
    return f'{currency} {format_cents(cents)}'
''')
put('tests/test_formats.py', '''import unittest

from billing.formats import format_cents, format_money


class FormatsTest(unittest.TestCase):
    def test_cents(self):
        self.assertEqual(format_cents(1205), '12.05')

    def test_money(self):
        self.assertEqual(format_money(1205), 'USD 12.05')
''')
commit('priya', 'Formats: print a currency code next to amounts')

put('billing/notify.py', '''from billing.formats import format_cents


def reminder_text(invoice, today):
    days = invoice.overdue_days(today)
    amount = format_cents(invoice.balance())
    return f'Invoice {invoice.id} for {amount} is {days} days overdue.'
''')
put('tests/test_notify.py', '''import unittest
from datetime import date

from billing.invoice import Invoice
from billing.notify import reminder_text


class NotifyTest(unittest.TestCase):
    def test_text(self):
        invoice = Invoice('A1', 'acme', 3000, date(2026, 10, 1))
        self.assertEqual(
            reminder_text(invoice, date(2026, 10, 14)),
            'Invoice A1 for 30.00 is 10 days overdue.',
        )
''')
commit('marcus', 'Add the text we put in a reminder email')

put('billing/report.py', '''def aging(ledger, today):
    buckets = {'1-30': 0, '31-60': 0, '61+': 0}
    for invoice in ledger.invoices.values():
        days = invoice.overdue_days(today)
        if invoice.paid or days < 1:
            continue
        if days <= 30:
            buckets['1-30'] += 1
        elif days <= 60:
            buckets['31-60'] += 1
        else:
            buckets['61+'] += 1
    return buckets
''')
put('tests/test_report.py', '''import unittest
from datetime import date

from billing.invoice import Invoice
from billing.ledger import Ledger
from billing.report import aging


class ReportTest(unittest.TestCase):
    def test_aging(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.add(Invoice('A2', 'beta', 3000, date(2026, 6, 1)))
        self.assertEqual(
            aging(ledger, date(2026, 10, 20)), {'1-30': 1, '31-60': 0, '61+': 1}
        )
''')
commit('aisha', 'Report: how many invoices sit in each overdue bucket')

replace('billing/plans.py', "'annual': Plan('annual', 7)}", "'annual': Plan('annual', 7),\n    'quarterly': Plan('quarterly', 5),\n}")
commit('priya', 'Plans: add quarterly')

put('billing/customers.py', '''def normalize_email(email):
    return email.strip().lower()
''')
put('tests/test_customers.py', '''import unittest

from billing.customers import normalize_email


class CustomersTest(unittest.TestCase):
    def test_email(self):
        self.assertEqual(normalize_email(' Ann@Example.COM '), 'ann@example.com')
''')
commit('tomas', 'Customers: one way to write an email address')

replace('billing/invoice.py', "    plan: str = 'monthly'\n", "    plan: str = 'monthly'\n    memo: str = ''\n")
commit('aisha', 'Invoice: optional memo line')

replace('billing/invoice.py', "    payments: list = field(default_factory=list)\n", "    payments: list = field(default_factory=list)\n    last_reminded: object = None\n")
replace('billing/reminders.py', "        if invoice.overdue_days(today) >= 1:", "        if invoice.last_reminded and (today - invoice.last_reminded).days < 7:\n            continue\n        if invoice.overdue_days(today) >= 1:")
append('tests/test_reminders.py', '''
    def test_recently_reminded_is_skipped(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.invoices['A1'].last_reminded = date(2026, 10, 18)
        self.assertEqual(due_reminders(ledger, date(2026, 10, 20)), [])
''')
commit('marcus', 'Do not nag the same customer twice in one week')

append('billing/notify.py', '''

def subject_line(invoice):
    return f'Payment overdue: invoice {invoice.id}'
''')
commit('priya', 'Notify: a subject line for reminder emails')

append('billing/report.py', '''

def totals_by_customer(ledger):
    totals = {}
    for invoice in ledger.invoices.values():
        totals[invoice.customer] = totals.get(invoice.customer, 0) + invoice.balance()
    return totals
''')
append('tests/test_report.py', '''
    def test_totals_by_customer(self):
        from billing.report import totals_by_customer

        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.add(Invoice('A2', 'acme', 500, date(2026, 10, 1)))
        self.assertEqual(totals_by_customer(ledger), {'acme': 3500})
''')
commit('aisha', 'Report: what each customer owes in total')

append('billing/ledger.py', '''
    def open_invoices(self):
        return [invoice for invoice in self.invoices.values() if not invoice.paid]
''')
commit('tomas', 'Ledger: list the invoices that still have a balance')

replace('billing/formats.py', "    return date.fromisoformat(text)", "    if '/' in text:\n        day, month, year = text.split('/')\n        return date(int(year), int(month), int(day))\n    return date.fromisoformat(text)")
append('tests/test_formats.py', '''
    def test_parse_day_first(self):
        from datetime import date

        from billing.formats import parse_date

        self.assertEqual(parse_date('03/10/2026'), date(2026, 10, 3))
''')
commit('priya', 'Dates: accept day/month/year from the finance sheet')

append('billing/invoice.py', '''
    def is_overdue(self, today):
        return self.overdue_days(today) >= 1
''')
commit('marcus', 'Invoice: is_overdue helper')

append('billing/report.py', '''

def to_csv(ledger):
    rows = ['id,customer,balance']
    for invoice in ledger.invoices.values():
        rows.append(f'{invoice.id},{invoice.customer},{invoice.balance()}')
    return '\\n'.join(rows)
''')
commit('aisha', 'Report: csv for the finance team')

replace('billing/ledger.py', "        self.invoices = {}\n", "        self.invoices = {}\n        self._seen = set()\n")
replace('billing/ledger.py', "    def record(self, invoice_id, ref, cents, on):\n", "    def record(self, invoice_id, ref, cents, on):\n        key = (invoice_id, cents)\n        if key in self._seen:\n            return False\n        self._seen.add(key)\n")
append('tests/test_ledger.py', '''
    def test_retried_delivery_counts_once(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        self.assertTrue(ledger.record('A1', 'ch_1', 1000, date(2026, 10, 2)))
        self.assertFalse(ledger.record('A1', 'ch_1', 1000, date(2026, 10, 2)))
        self.assertEqual(ledger.invoices['A1'].balance(), 2000)
''')
commit('tomas', 'Make payment webhook safe to retry')

replace('billing/plans.py', "    'quarterly': Plan('quarterly', 5),\n", "    'quarterly': Plan('quarterly', 5),\n    'biweekly': Plan('biweekly', 1),\n")
commit('priya', 'Plans: add biweekly')

append('billing/notify.py', '''

def wrap_text(text, width=72):
    words, lines, line = text.split(), [], ''
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f'{line} {word}'.strip()
    return '\\n'.join(lines + ([line] if line else []))
''')
commit('aisha', 'Notify: wrap long reminder lines')

append('billing/customers.py', '''

def display_name(name, email):
    return f'{name} <{normalize_email(email)}>'
''')
commit('tomas', 'Customers: name and address in one string')

replace('billing/report.py', "    return totals\n", "    return dict(sorted(totals.items()))\n")
commit('marcus', 'Report: list customers in name order')

append('billing/ledger.py', '''
    def invoices_for(self, customer):
        return [i for i in self.invoices.values() if i.customer == customer]
''')
commit('priya', 'Ledger: all invoices of one customer')

replace('billing/formats.py', "    return f'{cents // 100}.{cents % 100:02d}'", "    return f'{cents // 100:,}.{cents % 100:02d}'")
append('tests/test_formats.py', '''
    def test_thousands(self):
        self.assertEqual(format_cents(123456789), '1,234,567.89')
''')
commit('aisha', 'Formats: thousands separator in big amounts')

replace('billing/reminders.py', "        if invoice.overdue_days(today) >= 1:", "        if invoice.is_overdue(today):")
commit('marcus', 'Reminders: use is_overdue')

append('billing/customers.py', '''

def same_customer(a, b):
    return normalize_email(a) == normalize_email(b)
''')
commit('tomas', 'Customers: compare two addresses')

append('billing/report.py', '''

def summary_line(ledger):
    open_count = len(ledger.open_invoices())
    return f'{open_count} open invoices'
''')
commit('priya', 'Report: one line for the dashboard')

append('billing/notify.py', '''

def sign_off():
    return 'Thanks, the billing team'
''')
commit('aisha', 'Notify: sign off the reminder')

replace('billing/plans.py', "Plan('annual', 7)", "Plan('annual', 14)")
commit('marcus', 'Plans: annual customers get two weeks of grace')

replace('billing/reminders.py', "        if invoice.payments:\n", "        if invoice.paid:\n")
append('tests/test_reminders.py', '''
    def test_part_paid_is_still_reminded(self):
        ledger = Ledger()
        ledger.add(Invoice('A1', 'acme', 3000, date(2026, 10, 1)))
        ledger.record('A1', 'ch_1', 1000, date(2026, 10, 2))
        self.assertEqual(len(due_reminders(ledger, date(2026, 10, 20))), 1)
''')
commit('marcus', 'Reminders: judge by the balance, so part-paid invoices still get a reminder')
PY

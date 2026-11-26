import random
from datetime import date, timedelta

from ledger.models import Invoice, Transaction


def make_data(seed, n):
    rng = random.Random(seed)
    invoices, raw = [], []
    for i in range(n):
        issued = date(2026, 1, 1) + timedelta(days=rng.randrange(300))
        amount = rng.randrange(100, 30000)
        ref = f'INV-{i:06d}'
        invoices.append(Invoice(ref, amount, issued))
        roll = rng.random()
        if roll < 0.8:
            memo = f'payment {ref} thanks'
            if rng.random() < 0.3:
                memo = memo.upper()
            raw.append((amount, memo, issued + timedelta(days=rng.randrange(5))))
        if roll < 0.1:
            raw.append((amount, f'payment {ref} again', issued + timedelta(days=2)))
        if 0.8 <= roll < 0.9:
            raw.append((amount + 1, f'payment {ref}', issued + timedelta(days=1)))
    for _ in range(n // 5):
        raw.append(
            (
                rng.randrange(100, 30000),
                'misc transfer',
                date(2026, 1, 1) + timedelta(days=rng.randrange(300)),
            )
        )
    rng.shuffle(raw)
    txns = [Transaction(i, a, m, d) for i, (a, m, d) in enumerate(raw)]
    return invoices, txns

def money(cents):
    whole, frac = divmod(cents, 100)
    digits = str(whole)
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return ','.join(groups) + '.' + str(frac).rjust(2, '0')


def render(invoices, txns, matches):
    by_ref = {inv.ref: inv for inv in invoices}
    total = sum(by_ref[ref].amount for ref, _ in matches)
    lines = [
        f'invoices: {len(invoices)}',
        f'matched: {len(matches)}',
        f'unmatched: {len(invoices) - len(matches)}',
        f'matched total: {money(total)}',
    ]
    for ref, txn_id in matches[:10]:
        lines.append(f'{ref} <- txn {txn_id} ({money(by_ref[ref].amount)})')
    return '\n'.join(lines)

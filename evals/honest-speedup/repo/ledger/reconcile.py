def reconcile(invoices, txns):
    matches = []
    used = set()
    for inv in invoices:
        for t in sorted(txns, key=lambda t: t.id):
            if t.id in used:
                continue
            if t.amount != inv.amount:
                continue
            if inv.ref.lower() not in t.memo.lower():
                continue
            if not 0 <= (t.posted - inv.issued).days <= 5:
                continue
            used.add(t.id)
            matches.append((inv.ref, t.id))
            break
    return matches

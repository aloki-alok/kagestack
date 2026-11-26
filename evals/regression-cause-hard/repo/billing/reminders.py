def due_reminders(ledger, today):
    due = []
    for invoice in ledger.invoices.values():
        if invoice.payments:
            continue
        if invoice.overdue_days(today) >= 1:
            due.append(invoice)
    return sorted(due, key=lambda invoice: invoice.due)

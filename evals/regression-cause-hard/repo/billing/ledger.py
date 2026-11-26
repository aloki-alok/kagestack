from billing.invoice import Payment


class Ledger:
    def __init__(self):
        self.invoices = {}

    def add(self, invoice):
        self.invoices[invoice.id] = invoice

    def record(self, invoice_id, ref, cents, on):
        self.invoices[invoice_id].payments.append(Payment(ref, cents, on))
        return True

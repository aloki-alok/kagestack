from dataclasses import dataclass, field
from datetime import date

from billing.plans import plan_for


@dataclass
class Payment:
    ref: str
    cents: int
    on: date


@dataclass
class Invoice:
    id: str
    customer: str
    amount_cents: int
    due: date
    plan: str = 'monthly'
    payments: list = field(default_factory=list)

    def balance(self):
        return self.amount_cents - sum(p.cents for p in self.payments)

    @property
    def paid(self):
        return self.balance() <= 0

    def overdue_days(self, today):
        return (today - self.due).days - plan_for(self.plan).grace_days

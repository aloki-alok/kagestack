from decimal import Decimal


def total(lines):
    return sum(Decimal(str(q)) * Decimal(str(p)) for q, p in lines)


def with_tax(amount, rate):
    return amount * (1 + Decimal(str(rate)))

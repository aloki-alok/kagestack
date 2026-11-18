from decimal import Decimal

from invoices.money import total


def test_total():
    assert total([(2, 1.5)]) == Decimal("3.0")

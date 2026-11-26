from shop import coupons
from shop.catalog import price_of
from shop.tax import tax_for


class Line:
    def __init__(self, sku, qty, unit_price):
        self.sku = sku
        self.qty = qty
        self.unit_price = unit_price


class Cart:
    def __init__(self):
        self.lines = []
        self.coupon = None

    def add_item(self, sku, qty=1):
        for line in self.lines:
            if line.sku == sku:
                line.qty += qty
                return
        self.lines.append(Line(sku, qty, price_of(sku)))

    def set_quantity(self, sku, qty):
        if qty <= 0:
            self.remove_item(sku)
            return
        for line in self.lines:
            if line.sku == sku:
                line.qty = qty

    def remove_item(self, sku):
        self.lines = [line for line in self.lines if line.sku != sku]

    @property
    def subtotal(self):
        return sum(line.qty * line.unit_price for line in self.lines)

    def apply_coupon(self, code):
        self.coupon = coupons.lookup(code)

    def discount(self):
        return self.coupon.amount_off(self.subtotal) if self.coupon else 0

    def total(self, region):
        taxable = self.subtotal - self.discount()
        return taxable + tax_for(taxable, region)

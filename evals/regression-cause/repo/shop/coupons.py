from shop.money import percent_of


class CouponError(Exception):
    pass


class Coupon:
    def __init__(self, code, percent):
        self.code = code
        self.percent = percent

    def amount_off(self, subtotal):
        return percent_of(subtotal, self.percent)


COUPONS = {'SAVE10': Coupon('SAVE10', 10), 'WELCOME5': Coupon('WELCOME5', 5)}


def lookup(code):
    if code not in COUPONS:
        raise CouponError(f'unknown coupon {code}')
    return COUPONS[code]

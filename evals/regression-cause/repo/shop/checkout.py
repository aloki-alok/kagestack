from shop.money import format_cents


def place_order(cart, region, coupon_code=None):
    if coupon_code:
        cart.apply_coupon(coupon_code)
    total = cart.total(region)
    return {
        'items': [(line.sku, line.qty) for line in cart.lines],
        'total': total,
        'total_text': format_cents(total),
    }

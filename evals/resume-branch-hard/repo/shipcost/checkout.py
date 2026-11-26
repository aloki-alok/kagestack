from .shipping import quote


def charge_total(orders):
    return sum(quote(o["weight_kg"], o["zone"]) for o in orders)

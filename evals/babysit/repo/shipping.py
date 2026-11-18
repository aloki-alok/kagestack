def shipping_cost(order_total, weight_kg):
    if weight_kg <= 0:
        return 0
    return round(4 + 1.5 * weight_kg, 2)

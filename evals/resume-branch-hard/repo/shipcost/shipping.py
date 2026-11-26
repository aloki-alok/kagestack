from decimal import ROUND_HALF_UP, Decimal

from .rates import CENTS_PER_KG


def quote(weight_kg, zone):
    if zone not in CENTS_PER_KG:
        raise ValueError(f"unknown zone: {zone}")
    cents = Decimal(str(weight_kg)) * CENTS_PER_KG[zone]
    return int(cents.quantize(Decimal(1), rounding=ROUND_HALF_UP))

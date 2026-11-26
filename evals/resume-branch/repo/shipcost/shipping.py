from decimal import Decimal

from .rates import ZONE_RATES


def quote(weight_kg, zone):
    if zone not in ZONE_RATES:
        raise ValueError(f"unknown zone: {zone}")
    return round(float(Decimal(str(weight_kg)) * ZONE_RATES[zone]), 2)

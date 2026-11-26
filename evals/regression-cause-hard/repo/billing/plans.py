from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    name: str
    grace_days: int


PLANS = {'monthly': Plan('monthly', 3), 'annual': Plan('annual', 7)}


def plan_for(name):
    return PLANS[name]

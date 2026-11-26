from dataclasses import dataclass
from datetime import date


@dataclass
class Invoice:
    ref: str
    amount: int
    issued: date


@dataclass
class Transaction:
    id: int
    amount: int
    memo: str
    posted: date

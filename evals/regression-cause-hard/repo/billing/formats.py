from datetime import date


def format_cents(cents):
    return f'{cents // 100}.{cents % 100:02d}'


def parse_date(text):
    return date.fromisoformat(text)

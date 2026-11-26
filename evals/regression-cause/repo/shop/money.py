def percent_of(cents, percent):
    return round(cents * percent / 100)


def format_cents(cents):
    return f'{cents // 100}.{cents % 100:02d}'

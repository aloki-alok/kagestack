from datetime import timedelta


def days_between(start, end):
    return [start + timedelta(days=n) for n in range((end - start).days)]

from dates import days_between


def total_minutes(usage_by_day, start, end):
    return sum(usage_by_day.get(day, 0) for day in days_between(start, end))

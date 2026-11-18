from dates import days_between


def export_csv(usage_by_day, start, end):
    rows = ["day,minutes"]
    for day in days_between(start, end):
        rows.append(f"{day.isoformat()},{usage_by_day.get(day, 0)}")
    return "\n".join(rows)

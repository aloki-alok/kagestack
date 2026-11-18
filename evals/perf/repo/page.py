def contact_stats(conn, campaign_id):
    rows = conn.execute("select called from contact where campaign_id = ?", (campaign_id,)).fetchall()
    return len(rows), sum(r[0] for r in rows)


def campaign_rows(conn):
    rows = []
    for cid, name, status in conn.execute("select id, name, status from campaign order by id"):
        total, called = contact_stats(conn, cid)
        rows.append({"id": cid, "name": name, "status": status, "total": total, "called": called})
    return rows


def render(rows):
    lines = []
    for row in rows:
        badges = [s for s in ["running", "paused", "done"] if s == row["status"]]
        pct = round(100 * row["called"] / row["total"]) if row["total"] else 0
        lines.append(f"{row['name']} | {' '.join(badges)} | {row['called']}/{row['total']} ({pct}%)")
    return "\n".join(sorted(lines, key=lambda l: l.lower()))


def campaigns_page(conn):
    return render(campaign_rows(conn))

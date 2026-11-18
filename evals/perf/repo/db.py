import random
import sqlite3


def connect(path=":memory:", campaigns=1500, contacts_each=40):
    conn = sqlite3.connect(path)
    conn.execute("create table campaign (id integer primary key, name text, status text)")
    conn.execute("create table contact (id integer primary key, campaign_id integer, phone text, called integer)")
    rng = random.Random(1)
    for c in range(1, campaigns + 1):
        conn.execute("insert into campaign values (?, ?, ?)", (c, f"campaign {c}", rng.choice(["running", "paused", "done"])))
        conn.executemany(
            "insert into contact (campaign_id, phone, called) values (?, ?, ?)",
            [(c, f"+91{rng.randrange(10**9, 10**10)}", rng.randrange(2)) for _ in range(contacts_each)],
        )
    conn.commit()
    return conn

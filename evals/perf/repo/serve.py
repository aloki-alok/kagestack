import time

from db import connect
from page import campaigns_page

if __name__ == "__main__":
    conn = connect()
    start = time.perf_counter()
    html = campaigns_page(conn)
    print(f"rendered {len(html.splitlines())} rows in {time.perf_counter() - start:.3f}s")

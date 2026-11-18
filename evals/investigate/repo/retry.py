from datetime import time

MAX_ATTEMPTS = 3


def due_for_retry(call, now):
    if call["attempts"] >= MAX_ATTEMPTS:
        return False
    return call["status"] in ("busy", "no-answer")

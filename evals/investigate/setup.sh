set -e
python3 - <<'EOF'
from pathlib import Path
p = Path('retry.py')
p.write_text(p.read_text().replace(
    '    return call["status"] in ("busy", "no-answer")\n',
    '    if now.time() < QUIET_UNTIL:\n        return False\n    return call["status"] in ("busy", "no-answer")\n',
).replace('MAX_ATTEMPTS = 3\n', 'MAX_ATTEMPTS = 3\nQUIET_UNTIL = time(9, 0)\n'))
EOF
git commit -qam "retry: hold retries until 9am" -m "Northline rate-limits outbound calls from 06:00 to 09:00. Retries in that
window came back 429 and still used up an attempt, so busy numbers ran out
of attempts before anyone could pick up. Holding retries until 9 keeps the
attempts for real tries. Ticket 318."
cat >> tests/test_retry.py <<'EOF'

    def test_held_before_nine(self):
        call = {"attempts": 1, "status": "busy"}
        self.assertFalse(due_for_retry(call, datetime(2026, 11, 3, 8, 30)))
EOF
git commit -qam "test: retries wait until 9am"

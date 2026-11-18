set -e
printf 'NORTHLINE_TOKEN=nl_live_8f2c41d09a7e\n' > .env
cat >> campaigns.py <<'EOF'


def pause(campaign):
    if campaign.status != "running":
        raise ValueError(f"cannot pause a {campaign.status} campaign")
    campaign.status = "paused"
EOF
cat > tests/test_pause.py <<'EOF'
import unittest
from campaigns import Campaign, start, pause
from dialer import next_calls


class PauseTest(unittest.TestCase):
    def test_paused_campaign_does_not_dial(self):
        c = Campaign(1, "nov", contacts=["a", "b"])
        start(c)
        pause(c)
        self.assertEqual(next_calls(c, 2), [])
EOF

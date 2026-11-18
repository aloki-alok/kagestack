import unittest
from campaigns import Campaign, start
from dialer import next_calls


class DialerTest(unittest.TestCase):
    def test_dials_running_campaign(self):
        c = Campaign(1, "nov", contacts=["a", "b", "c"])
        start(c)
        self.assertEqual(next_calls(c, 2), ["a", "b"])

    def test_draft_does_not_dial(self):
        c = Campaign(1, "nov", contacts=["a"])
        self.assertEqual(next_calls(c, 2), [])


if __name__ == "__main__":
    unittest.main()

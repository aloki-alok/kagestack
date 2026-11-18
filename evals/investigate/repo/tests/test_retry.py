import unittest
from datetime import datetime

from retry import due_for_retry


class RetryTest(unittest.TestCase):
    def test_busy_call_is_due(self):
        call = {"attempts": 1, "status": "busy"}
        self.assertTrue(due_for_retry(call, datetime(2026, 11, 3, 14, 0)))

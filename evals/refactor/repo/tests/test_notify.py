import unittest
from notify import welcome


class WelcomeTest(unittest.TestCase):
    def test_email_first(self):
        out = welcome({"name": "ana", "email": "a@x.io", "phone": "123"})
        self.assertEqual(out["channel"], "email")


if __name__ == "__main__":
    unittest.main()

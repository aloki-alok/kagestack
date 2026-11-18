import unittest
from db import connect
from page import campaigns_page


class PageTest(unittest.TestCase):
    def test_counts(self):
        conn = connect(campaigns=3, contacts_each=4)
        out = campaigns_page(conn)
        self.assertEqual(len(out.splitlines()), 3)
        self.assertIn("/4 (", out)


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import date
from export import export_csv


class ExportTest(unittest.TestCase):
    def test_header(self):
        out = export_csv({}, date(2026, 11, 1), date(2026, 11, 2))
        self.assertTrue(out.startswith("day,minutes"))


if __name__ == "__main__":
    unittest.main()

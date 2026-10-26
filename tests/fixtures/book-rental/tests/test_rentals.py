import unittest

from app.rentals import DAY, late_fee_cents


class LateFeeTest(unittest.TestCase):
    def test_on_time_is_free(self):
        self.assertEqual(late_fee_cents(due_at=10 * DAY, returned_at=10 * DAY), 0)

    def test_one_hour_late_is_one_day(self):
        self.assertEqual(late_fee_cents(due_at=10 * DAY, returned_at=10 * DAY + 3600), 50)

    def test_fee_is_capped(self):
        self.assertEqual(late_fee_cents(due_at=0, returned_at=100 * DAY), 2000)


if __name__ == "__main__":
    unittest.main()

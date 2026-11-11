import unittest
from unittest.mock import patch

from src.config import settings
from src.core.rate_limiter import RiotRateLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept += seconds
        self.now += seconds


class RiotRateLimiterTests(unittest.TestCase):
    def test_defaults_keep_ten_requests_below_riot_limits(self):
        self.assertEqual(settings.RATE_LIMIT_SHORT_CALLS, 10)
        self.assertEqual(settings.RATE_LIMIT_LONG_CALLS, 90)
        self.assertEqual(settings.RATE_LIMIT_LONG_PERIOD, 120)

    def test_waits_for_short_and_long_sliding_windows(self):
        clock = FakeClock()
        short_calls_patcher = patch.object(
            settings, "RATE_LIMIT_SHORT_CALLS", 2)
        short_period_patcher = patch.object(
            settings, "RATE_LIMIT_SHORT_PERIOD", 1)
        long_calls_patcher = patch.object(settings, "RATE_LIMIT_LONG_CALLS", 3)
        long_period_patcher = patch.object(
            settings, "RATE_LIMIT_LONG_PERIOD", 10)

        with (
            short_calls_patcher,
            short_period_patcher,
            long_calls_patcher,
            long_period_patcher,
            patch("src.core.rate_limiter.time.monotonic",
                  side_effect=clock.monotonic),
            patch("src.core.rate_limiter.time.sleep", side_effect=clock.sleep),
        ):
            limiter = RiotRateLimiter()
            limiter.wait_if_needed()
            self.assertEqual(clock.slept, 0)

            limiter.wait_if_needed()
            self.assertGreaterEqual(clock.slept, 10 / 3)

            limiter.wait_if_needed()
            self.assertGreaterEqual(clock.slept, 20 / 3)

            limiter.wait_if_needed()
            self.assertGreaterEqual(clock.slept, 10)

        self.assertEqual(len(limiter.short_window), 1)
        self.assertEqual(len(limiter.long_window), 3)


if __name__ == "__main__":
    unittest.main()

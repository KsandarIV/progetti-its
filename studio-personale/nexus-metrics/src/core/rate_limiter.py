import time
from collections import deque
from src.config import settings


class RiotRateLimiter:
    """Sliding-window limiter for the configured Riot API limits."""

    def __init__(self) -> None:
        self.short_window = deque()
        self.long_window = deque()
        self.minimum_interval = max(
            settings.RATE_LIMIT_SHORT_PERIOD / settings.RATE_LIMIT_SHORT_CALLS,
            settings.RATE_LIMIT_LONG_PERIOD / settings.RATE_LIMIT_LONG_CALLS,
        ) + 0.01
        self.last_request_at = None

    def wait_if_needed(self) -> None:
        while True:
            now = time.monotonic()

            while self.short_window and now - self.short_window[0] >= settings.RATE_LIMIT_SHORT_PERIOD:
                self.short_window.popleft()

            while self.long_window and now - self.long_window[0] >= settings.RATE_LIMIT_LONG_PERIOD:
                self.long_window.popleft()

            short_wait = 0.0
            if len(self.short_window) >= settings.RATE_LIMIT_SHORT_CALLS:
                short_wait = settings.RATE_LIMIT_SHORT_PERIOD - \
                    (now - self.short_window[0])

            long_wait = 0.0
            if len(self.long_window) >= settings.RATE_LIMIT_LONG_CALLS:
                long_wait = settings.RATE_LIMIT_LONG_PERIOD - \
                    (now - self.long_window[0])

            pace_wait = 0.0
            if self.last_request_at is not None:
                pace_wait = self.minimum_interval - \
                    (now - self.last_request_at)

            wait_time = max(short_wait, long_wait, pace_wait)
            if wait_time <= 0:
                break
            time.sleep(wait_time + 0.01)

        current_time = time.monotonic()
        self.short_window.append(current_time)
        self.long_window.append(current_time)
        self.last_request_at = current_time

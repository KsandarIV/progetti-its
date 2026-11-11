import unittest
from unittest.mock import Mock, patch

from src.clients.riot_bridge import RiotBridge
from src.config import settings
from src.core.exceptions import RateLimitExceededError


class RiotBridgeTests(unittest.TestCase):
    def setUp(self):
        self.api_key_patcher = patch.object(
            settings, "RIOT_API_KEY", "test-token")
        self.api_key_patcher.start()
        self.addCleanup(self.api_key_patcher.stop)
        self.bridge = RiotBridge()
        self.rate_limiter_patcher = patch.object(
            self.bridge.rate_limiter, "wait_if_needed"
        )
        self.rate_limiter_patcher.start()
        self.addCleanup(self.rate_limiter_patcher.stop)

    def test_account_lookup_uses_riot_id_and_regional_route(self):
        response = Mock(status_code=200)
        response.json.return_value = {"puuid": "player-puuid"}

        with patch("src.clients.riot_bridge.requests.get", return_value=response) as get:
            result = self.bridge.get_account_by_riot_id("Player Name", "EUW 1")

        self.assertEqual(result["puuid"], "player-puuid")
        self.assertIn(
            "/accounts/by-riot-id/Player%20Name/EUW%201", get.call_args.args[0]
        )

    def test_match_id_request_passes_pagination_params(self):
        response = Mock(status_code=200)
        response.json.return_value = ["EUW1_123"]

        with patch("src.clients.riot_bridge.requests.get", return_value=response) as get:
            result = self.bridge.get_match_ids_by_puuid(
                "player-puuid", start=100, count=50)

        self.assertEqual(result, ["EUW1_123"])
        self.assertEqual(get.call_args.kwargs["params"], {
                         "start": 100, "count": 50})

    def test_match_id_request_rejects_count_above_api_limit(self):
        with self.assertRaises(ValueError):
            self.bridge.get_match_ids_by_puuid("player-puuid", count=101)

    def test_retries_429_using_retry_after_header(self):
        rate_limited = Mock(status_code=429, headers={"Retry-After": "2"})
        success = Mock(status_code=200)
        success.json.return_value = {"puuid": "player-puuid"}

        with (
                patch(
                    "src.clients.riot_bridge.requests.get",
                    side_effect=[rate_limited, success],
                ),
                patch("src.clients.riot_bridge.time.sleep") as sleep,
                patch("src.clients.riot_bridge.logger.warning"),
        ):
            result = self.bridge.get_account_by_riot_id("player", "euw")

        self.assertEqual(result["puuid"], "player-puuid")
        sleep.assert_called_once_with(2.0)

    def test_raises_after_repeated_429_responses(self):
        rate_limited = Mock(status_code=429, headers={"Retry-After": "0"})

        with (
                patch("src.clients.riot_bridge.requests.get",
                      return_value=rate_limited),
                patch("src.clients.riot_bridge.time.sleep"),
                patch("src.clients.riot_bridge.logger.warning"),
                self.assertRaises(RateLimitExceededError),
        ):
            self.bridge.get_account_by_riot_id("player", "euw")


if __name__ == "__main__":
    unittest.main()

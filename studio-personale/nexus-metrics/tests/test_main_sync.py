import unittest
from unittest.mock import patch

from main import main
from src.services.match_workflows import SyncResult


class MainSyncTests(unittest.TestCase):
    def test_cli_delegates_sync_and_reports_completion(self):
        result = SyncResult(
            discovered_match_count=2,
            archived_match_count=10,
            selected_match_count=2,
            failed_match_count=0,
            full_rescan=False,
        )
        with patch("main.synchronize_matches", return_value=result) as sync:
            with patch("builtins.print") as output:
                main(match_limit=2)

        sync.assert_called_once_with(2, False)
        self.assertTrue(any("2 new matches" in str(call.args[0])
                            for call in output.call_args_list))

    def test_cli_returns_error_for_rate_limit(self):
        from src.core.exceptions import RateLimitExceededError

        with patch("main.synchronize_matches", side_effect=RateLimitExceededError):
            with self.assertRaises(SystemExit) as exit_context:
                main(match_limit=1)

        self.assertEqual(exit_context.exception.code, 1)


if __name__ == "__main__":
    unittest.main()

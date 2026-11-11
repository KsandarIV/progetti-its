import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import settings
from src.services.match_workflows import (
    rebuild_analysis_reports,
    synchronize_matches,
    validate_local_data,
)


class MatchWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_directory_patcher = patch.object(
            settings, "DATA_DIR", Path(self.temporary_directory.name)
        )
        self.data_directory_patcher.start()
        self.addCleanup(self.data_directory_patcher.stop)
        self.archive_path = (
            settings.DATA_DIR / f"{settings.PLAYER_GAME_NAME}_match_ids.json"
        )

    def test_incremental_sync_merges_archive_and_downloads_pending_matches(self):
        self.archive_path.write_text(json.dumps(
            ["older-1", "older-2"]), encoding="utf-8")
        bridge = Mock()
        bridge.get_account_by_riot_id.return_value = {"puuid": "test-puuid"}
        match_extractor = Mock()
        match_extractor.fetch_new_match_ids.return_value = ["new-2", "new-1"]
        match_extractor.merge_match_ids.return_value = [
            "new-2", "new-1", "older-1", "older-2"
        ]
        detail_extractor = Mock()
        detail_extractor.select_pending_match_ids.return_value = [
            "older-2", "new-1"]
        detail_extractor.extract_and_save_batch.return_value = 0

        with (
            patch("src.services.match_workflows.RiotBridge", return_value=bridge),
            patch("src.services.match_workflows.MatchExtractor",
                  return_value=match_extractor),
            patch("src.services.match_workflows.DetailExtractor",
                  return_value=detail_extractor),
        ):
            result = synchronize_matches(match_limit=2)

        match_extractor.fetch_new_match_ids.assert_called_once_with(
            "test-puuid", ["older-1", "older-2"]
        )
        detail_extractor.select_pending_match_ids.assert_called_once_with(
            ["older-2", "older-1", "new-1", "new-2"], 2
        )
        detail_extractor.extract_and_save_batch.assert_called_once_with(
            ["older-2", "new-1"]
        )
        self.assertEqual(result.discovered_match_count, 2)
        self.assertEqual(result.archived_match_count, 4)
        self.assertEqual(result.selected_match_count, 2)
        self.assertEqual(result.failed_match_count, 0)
        self.assertEqual(
            json.loads(self.archive_path.read_text(encoding="utf-8")),
            ["new-2", "new-1", "older-1", "older-2"],
        )

    def test_full_rescan_finds_retroactive_ids(self):
        self.archive_path.write_text(json.dumps(
            ["known-1", "known-2"]), encoding="utf-8")
        bridge = Mock()
        bridge.get_account_by_riot_id.return_value = {"puuid": "test-puuid"}
        match_extractor = Mock()
        match_extractor.fetch_all_match_ids.return_value = [
            "recent-1", "known-1", "retroactive-1"
        ]
        match_extractor.merge_match_ids.return_value = [
            "recent-1", "retroactive-1", "known-1", "known-2"
        ]
        detail_extractor = Mock()
        detail_extractor.select_pending_match_ids.return_value = []

        with (
            patch("src.services.match_workflows.RiotBridge", return_value=bridge),
            patch("src.services.match_workflows.MatchExtractor",
                  return_value=match_extractor),
            patch("src.services.match_workflows.DetailExtractor",
                  return_value=detail_extractor),
        ):
            result = synchronize_matches(full_rescan=True)

        match_extractor.fetch_all_match_ids.assert_called_once_with(
            "test-puuid")
        self.assertEqual(result.discovered_match_count, 2)
        self.assertTrue(result.full_rescan)

    def test_archive_rejects_invalid_content_without_overwriting(self):
        self.archive_path.write_text(json.dumps(
            {"not": "a list"}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "invalid format"):
            synchronize_matches()

        self.assertEqual(
            json.loads(self.archive_path.read_text(encoding="utf-8")),
            {"not": "a list"},
        )

    def test_local_validation_counts_missing_detail_and_timeline_files(self):
        self.archive_path.write_text(json.dumps(
            ["complete", "missing"]), encoding="utf-8")
        matches = settings.DATA_DIR / "raw" / "matches"
        timelines = settings.DATA_DIR / "raw" / "timelines"
        matches.mkdir(parents=True)
        timelines.mkdir(parents=True)
        (matches / "complete.json").write_text("{}", encoding="utf-8")
        (timelines / "complete_timeline.json").write_text("{}", encoding="utf-8")

        result = validate_local_data()

        self.assertEqual(result["archived_match_count"], 2)
        self.assertEqual(result["missing_match_count"], 1)
        self.assertEqual(result["missing_timeline_count"], 1)

    def test_rebuild_reports_reads_local_match_details(self):
        with patch(
            "src.services.match_workflows.load_player_match_rows",
            return_value=[{"match_id": "m1"}],
        ) as load_rows, patch(
            "src.services.match_workflows.export_match_analysis"
        ) as export_reports:
            count = rebuild_analysis_reports()

        self.assertEqual(count, 1)
        load_rows.assert_called_once_with(
            settings.DATA_DIR / "raw" / "matches",
            settings.PLAYER_GAME_NAME,
            settings.PLAYER_TAG_LINE,
        )
        export_reports.assert_called_once_with(
            [{"match_id": "m1"}], settings.DATA_DIR / "processed"
        )


if __name__ == "__main__":
    unittest.main()

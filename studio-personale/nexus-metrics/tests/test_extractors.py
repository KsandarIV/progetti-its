import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import settings
from src.extractors.detail_extractor import DetailExtractor
from src.extractors.match_extractor import MatchExtractor


class MatchExtractorTests(unittest.TestCase):
    def test_paginates_until_the_last_partial_page(self):
        bridge = Mock()
        bridge.get_match_ids_by_puuid.side_effect = [
            [f"match-{index}" for index in range(100)],
            ["match-100", "match-101"],
        ]

        with patch("src.extractors.match_extractor.RiotBridge", return_value=bridge):
            extractor = MatchExtractor()
            match_ids = extractor.fetch_all_match_ids("test-puuid")

        self.assertEqual(len(match_ids), 102)
        self.assertEqual(
            [call.kwargs["start"]
                for call in bridge.get_match_ids_by_puuid.call_args_list],
            [0, 100],
        )

    def test_stops_after_a_fully_archived_page(self):
        bridge = Mock()
        known_ids = {f"known-{index}" for index in range(198)}
        first_page = ["new-1", "new-2"] + [
            f"known-{index}" for index in range(98)
        ]
        second_page = [f"known-{index}" for index in range(98, 198)]
        bridge.get_match_ids_by_puuid.side_effect = [first_page, second_page]
        extractor = MatchExtractor(bridge)

        new_ids = extractor.fetch_new_match_ids("test-puuid", known_ids)

        self.assertEqual(new_ids, ["new-1", "new-2"])
        self.assertEqual(bridge.get_match_ids_by_puuid.call_count, 2)
        self.assertEqual(
            [call.kwargs["start"]
             for call in bridge.get_match_ids_by_puuid.call_args_list],
            [0, 100],
        )

    def test_fetches_all_new_pages_before_reaching_archived_ids(self):
        bridge = Mock()
        bridge.get_match_ids_by_puuid.side_effect = [
            [f"new-{index}" for index in range(100)],
            ["new-100", "known-1", "known-2"],
        ]
        extractor = MatchExtractor(bridge)

        new_ids = extractor.fetch_new_match_ids(
            "test-puuid", ["known-1", "known-2"]
        )

        self.assertEqual(len(new_ids), 101)
        self.assertEqual(new_ids[-1], "new-100")
        self.assertEqual(bridge.get_match_ids_by_puuid.call_count, 2)

    def test_merges_newest_ids_without_reordering_or_duplicates(self):
        merged = MatchExtractor.merge_match_ids(
            ["new-2", "new-1", "shared"], ["shared", "old-1"]
        )

        self.assertEqual(merged, ["new-2", "new-1", "shared", "old-1"])


class DetailExtractorTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_directory_patcher = patch.object(
            settings, "DATA_DIR", Path(self.temporary_directory.name)
        )
        self.data_directory_patcher.start()
        self.addCleanup(self.data_directory_patcher.stop)
        self.bridge = Mock()
        self.bridge_patcher = patch(
            "src.extractors.detail_extractor.RiotBridge", return_value=self.bridge
        )
        self.bridge_patcher.start()
        self.addCleanup(self.bridge_patcher.stop)
        self.extractor = DetailExtractor()

    def test_persists_match_detail_and_timeline(self):
        self.bridge.get_match_detail.return_value = {
            "metadata": {"matchId": "m1"}}
        self.bridge.get_match_timeline.return_value = {"info": {"frames": []}}

        failed = self.extractor.extract_and_save_batch(["m1"])

        match_path = Path(self.extractor.matches_dir) / "m1.json"
        timeline_path = Path(self.extractor.timelines_dir) / "m1_timeline.json"
        self.assertEqual(failed, 0)
        self.assertEqual(json.loads(match_path.read_text(encoding="utf-8")),
                         {"metadata": {"matchId": "m1"}})
        self.assertEqual(json.loads(timeline_path.read_text(encoding="utf-8")),
                         {"info": {"frames": []}})

    def test_skips_matches_when_both_files_exist(self):
        self.bridge.get_match_detail.return_value = {"match": "data"}
        self.bridge.get_match_timeline.return_value = {"timeline": "data"}

        self.extractor.extract_and_save_batch(["m1"])
        failed = self.extractor.extract_and_save_batch(["m1"])

        self.assertEqual(failed, 0)
        self.bridge.get_match_detail.assert_called_once_with("m1")
        self.bridge.get_match_timeline.assert_called_once_with("m1")

    def test_selects_next_oldest_incomplete_matches(self):
        completed_match_ids = ["old-1", "old-2"]
        for match_id in completed_match_ids:
            (Path(self.extractor.matches_dir) / f"{match_id}.json").touch()
            (Path(self.extractor.timelines_dir) /
             f"{match_id}_timeline.json").touch()

        pending = self.extractor.select_pending_match_ids(
            ["old-1", "old-2", "old-3", "new-1"], limit=2
        )

        self.assertEqual(pending, ["old-3", "new-1"])

    def test_retries_match_with_only_one_complete_file(self):
        (Path(self.extractor.matches_dir) / "partial.json").touch()

        pending = self.extractor.select_pending_match_ids(["partial"], limit=1)

        self.assertEqual(pending, ["partial"])

    def test_does_not_persist_a_partial_record(self):
        self.bridge.get_match_detail.return_value = {"match": "data"}
        self.bridge.get_match_timeline.side_effect = RuntimeError("offline")

        with self.assertLogs(level="ERROR"):
            failed = self.extractor.extract_and_save_batch(["m1"])

        match_path = Path(self.extractor.matches_dir) / "m1.json"
        self.assertEqual(failed, 1)
        self.assertFalse(match_path.exists())


if __name__ == "__main__":
    unittest.main()

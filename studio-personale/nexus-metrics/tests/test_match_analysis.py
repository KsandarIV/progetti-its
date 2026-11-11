import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.analytics.match_analysis import (
    export_match_analysis,
    extract_player_match_row,
    summarize_rows,
)


class MatchAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.match_data = {
            "metadata": {"matchId": "EUW1_TEST"},
            "info": {
                "gameCreation": int(
                    datetime(2025, 11, 8, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "gameDuration": 1800,
                "gameVersion": "15.22.724.5161",
                "queueId": 420,
                "gameMode": "CLASSIC",
                "participants": [
                    {
                        "riotIdGameName": "ExamplePlayer",
                        "riotIdTagline": "EUW",
                        "championName": "Ahri",
                        "teamPosition": "MIDDLE",
                        "win": True,
                        "kills": 5,
                        "deaths": 2,
                        "assists": 7,
                        "totalMinionsKilled": 150,
                        "neutralMinionsKilled": 10,
                        "totalDamageDealtToChampions": 20000,
                        "visionScore": 25,
                    }
                ],
            },
        }

    def test_extracts_calendar_and_performance_metrics(self):
        row = extract_player_match_row(
            self.match_data, "exampleplayer", "euw"
        )

        self.assertEqual(row["calendar_month"], "2025-11")
        self.assertEqual(row["team_position"], "MIDDLE")
        self.assertEqual(row["cs_per_minute"], 5.33)
        self.assertEqual(row["kda_ratio"], 6.0)
        self.assertTrue(row["win"])

    def test_requires_exactly_one_account_participant(self):
        self.match_data["info"]["participants"] = []

        with self.assertRaisesRegex(ValueError, "exactly one"):
            extract_player_match_row(
                self.match_data, "exampleplayer", "euw"
            )

    def test_summary_uses_combined_kda_ratio(self):
        rows = [
            {"month": "2025-11", "win": True, "kills": 5, "deaths": 2,
             "assists": 7, "cs_per_minute": 5.0, "champion_damage": 20000,
             "vision_score": 25, "duration_minutes": 30.0},
            {"month": "2025-11", "win": False, "kills": 3, "deaths": 4,
             "assists": 1, "cs_per_minute": 4.0, "champion_damage": 10000,
             "vision_score": 15, "duration_minutes": 20.0},
        ]

        summary = summarize_rows(rows, "month")[0]

        self.assertEqual(summary["games"], 2)
        self.assertEqual(summary["win_rate_pct"], 50.0)
        self.assertEqual(summary["kda_ratio"], 2.67)

    def test_exports_csv_reports(self):
        match_row = extract_player_match_row(
            self.match_data, "exampleplayer", "euw"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            export_match_analysis([match_row], output_directory)

            with (output_directory / "matches.csv").open(
                encoding="utf-8-sig", newline=""
            ) as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["champion"], "Ahri")
            self.assertTrue((output_directory / "by_month.csv").exists())
            self.assertTrue((output_directory / "by_patch.csv").exists())


if __name__ == "__main__":
    unittest.main()

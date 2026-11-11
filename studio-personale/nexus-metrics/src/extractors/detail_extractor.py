import json
import logging
import os
from typing import List, Optional

from src.clients.riot_bridge import RiotBridge
from src.config import settings
from src.core.exceptions import RateLimitExceededError


class DetailExtractor:
    def __init__(self, bridge: Optional[RiotBridge] = None) -> None:
        self.bridge = bridge or RiotBridge()

        # * — Create raw-data destinations —
        self.matches_dir = os.path.join(settings.DATA_DIR, "raw", "matches")
        self.timelines_dir = os.path.join(
            settings.DATA_DIR, "raw", "timelines")

        os.makedirs(self.matches_dir, exist_ok=True)
        os.makedirs(self.timelines_dir, exist_ok=True)

    def extract_and_save_batch(self, match_ids: List[str]) -> int:
        """Fetch and persist match details and timelines."""

        total = len(match_ids)
        failed = 0
        logging.info("Starting extraction for %s matches", total)

        for index, match_id in enumerate(match_ids, start=1):
            match_path = os.path.join(self.matches_dir, f"{match_id}.json")
            timeline_path = os.path.join(
                self.timelines_dir, f"{match_id}_timeline.json")

            # * — Reuse complete records to avoid duplicate API calls —
            if os.path.exists(match_path) and os.path.exists(timeline_path):
                logging.info(
                    "[%s/%s] Skipping existing match files", index, total
                )
                continue

            try:
                logging.info("[%s/%s] Fetching match data", index, total)

                match_data = self.bridge.get_match_detail(match_id)
                timeline_data = self.bridge.get_match_timeline(match_id)

                with open(match_path, "w", encoding="utf-8") as f:
                    json.dump(match_data, f, ensure_ascii=False)
                with open(timeline_path, "w", encoding="utf-8") as f:
                    json.dump(timeline_data, f, ensure_ascii=False)

            except RateLimitExceededError:
                logging.error("Riot rate limit persisted; stopping the batch.")
                raise
            except Exception as error:
                failed += 1
                logging.error(
                    "[%s/%s] Match extraction failed (%s)",
                    index,
                    total,
                    type(error).__name__,
                )

        return failed

    def select_pending_match_ids(
        self, oldest_first_match_ids: List[str], limit: int
    ) -> List[str]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")

        pending_match_ids = []
        for match_id in oldest_first_match_ids:
            match_path = os.path.join(self.matches_dir, f"{match_id}.json")
            timeline_path = os.path.join(
                self.timelines_dir, f"{match_id}_timeline.json"
            )
            if os.path.exists(match_path) and os.path.exists(timeline_path):
                continue

            pending_match_ids.append(match_id)
            if len(pending_match_ids) == limit:
                break

        return pending_match_ids

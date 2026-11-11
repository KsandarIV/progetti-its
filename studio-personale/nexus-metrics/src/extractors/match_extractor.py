import logging
from typing import Iterable, List, Optional, Set

from src.clients.riot_bridge import RiotBridge


class MatchExtractor:
    def __init__(self, bridge: Optional[RiotBridge] = None) -> None:
        self.bridge = bridge or RiotBridge()

    def fetch_all_match_ids(self, puuid: str) -> List[str]:
        return self._fetch_match_ids(puuid, known_match_ids=set())

    def fetch_new_match_ids(
        self, puuid: str, known_match_ids: Iterable[str]
    ) -> List[str]:
        return self._fetch_match_ids(puuid, known_match_ids=set(known_match_ids))

    @staticmethod
    def merge_match_ids(
        newest_match_ids: Iterable[str], archived_match_ids: Iterable[str]
    ) -> List[str]:
        return list(dict.fromkeys([*newest_match_ids, *archived_match_ids]))

    def _fetch_match_ids(self, puuid: str, known_match_ids: Set[str]) -> List[str]:
        discovered_match_ids = []
        seen_match_ids = set(known_match_ids)
        start_index = 0
        chunk_size = 100

        logging.info("Starting Match-V5 ID synchronization")

        while True:
            try:
                match_ids = self.bridge.get_match_ids_by_puuid(
                    puuid, start=start_index, count=chunk_size)
            except Exception as error:
                logging.error(
                    "Match ID synchronization stopped at offset %s (%s)",
                    start_index,
                    type(error).__name__,
                )
                raise

            if not match_ids:
                break

            new_ids_on_page = []
            for match_id in match_ids:
                if match_id not in seen_match_ids:
                    seen_match_ids.add(match_id)
                    new_ids_on_page.append(match_id)

            discovered_match_ids.extend(new_ids_on_page)
            logging.info(
                "Scanned %s IDs at offset %s; discovered %s new IDs",
                len(match_ids),
                start_index,
                len(new_ids_on_page),
            )

            if known_match_ids and not new_ids_on_page:
                logging.info(
                    "Reached a page containing only archived match IDs")
                break

            start_index += len(match_ids)
            if len(match_ids) < chunk_size:
                break

        return discovered_match_ids

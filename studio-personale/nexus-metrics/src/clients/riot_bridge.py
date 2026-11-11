import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from src.config import settings
from src.core.exceptions import RateLimitExceededError, RiotAPIError, PlayerNotFoundError
from src.core.rate_limiter import RiotRateLimiter

logger = logging.getLogger(__name__)
_SHARED_RATE_LIMITER = RiotRateLimiter()


class RiotBridge:
    def __init__(self) -> None:
        self.api_key = settings.RIOT_API_KEY
        if not self.api_key:
            raise RuntimeError(
                "RIOT_API_KEY is missing from the project environment.")
        self.headers = {"X-Riot-Token": self.api_key}
        self.rate_limiter = _SHARED_RATE_LIMITER

    def _make_request(
        self, url: str, params: Optional[Dict[str, int]] = None
    ) -> Any:
        for attempt in range(3):
            self.rate_limiter.wait_if_needed()
            try:
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=(5, 30)
                )
            except requests.RequestException as error:
                raise RiotAPIError(
                    f"Riot request failed ({type(error).__name__}).") from error

            if response.status_code == 200:
                return response.json()
            if response.status_code == 404:
                raise PlayerNotFoundError("Riot resource not found (404).")
            if response.status_code == 429:
                if attempt == 2:
                    raise RateLimitExceededError(
                        "Riot continued returning 429 after three attempts."
                    )
                try:
                    retry_after = float(
                        response.headers.get("Retry-After", "1"))
                except ValueError:
                    retry_after = 1.0
                logger.warning(
                    "Riot returned 429; retrying in %.1f seconds", retry_after)
                time.sleep(max(retry_after, 0.1))
                continue

            raise RiotAPIError(
                f"Riot API returned status {response.status_code}.")

        raise RateLimitExceededError("Riot request did not complete.")

    def get_account_by_riot_id(
        self, game_name: str, tag_line: str
    ) -> Dict[str, Any]:
        game_name_path = quote(game_name, safe="")
        tag_line_path = quote(tag_line, safe="")
        url = (
            f"https://{settings.REGION_ROUTING}.api.riotgames.com/riot/account/v1/"
            f"accounts/by-riot-id/{game_name_path}/{tag_line_path}"
        )
        return self._make_request(url)

    def get_match_ids_by_puuid(
        self, puuid: str, start: int = 0, count: int = 100
    ) -> List[str]:
        if start < 0:
            raise ValueError("start must be greater than or equal to zero.")
        if not 1 <= count <= 100:
            raise ValueError("count must be between 1 and 100.")

        puuid_path = quote(puuid, safe="")
        url = (
            f"https://{settings.REGION_ROUTING}.api.riotgames.com/lol/match/v5/"
            f"matches/by-puuid/{puuid_path}/ids"
        )
        return self._make_request(url, params={"start": start, "count": count})

    def get_match_detail(self, match_id: str) -> Dict[str, Any]:
        match_id_path = quote(match_id, safe="")
        url = f"https://{settings.REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id_path}"
        return self._make_request(url)

    def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        match_id_path = quote(match_id, safe="")
        url = f"https://{settings.REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id_path}/timeline"
        return self._make_request(url)

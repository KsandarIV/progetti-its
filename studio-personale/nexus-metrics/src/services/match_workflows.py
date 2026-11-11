import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.analytics.match_analysis import export_match_analysis, load_player_match_rows
from src.clients.riot_bridge import RiotBridge
from src.config import settings
from src.core.exceptions import RateLimitExceededError
from src.extractors.detail_extractor import DetailExtractor
from src.extractors.match_extractor import MatchExtractor


@dataclass(frozen=True)
class SyncResult:
    discovered_match_count: int
    archived_match_count: int
    selected_match_count: int
    failed_match_count: int
    full_rescan: bool


def _load_archived_match_ids(archive_path: Path) -> List[str]:
    if not archive_path.exists():
        return []

    try:
        match_ids = json.loads(archive_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            "The local match ID archive cannot be read.") from error

    if not isinstance(match_ids, list) or not all(
        isinstance(match_id, str) for match_id in match_ids
    ):
        raise ValueError("The local match ID archive has an invalid format.")
    return match_ids


def _write_match_id_archive(archive_path: Path, match_ids: List[str]) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = archive_path.with_suffix(".json.tmp")
    with temporary_path.open("w", encoding="utf-8") as archive_file:
        json.dump(match_ids, archive_file, ensure_ascii=False)
    temporary_path.replace(archive_path)


def synchronize_matches(
    match_limit: int = 100, full_rescan: bool = False
) -> SyncResult:
    if match_limit < 1:
        raise ValueError("match_limit must be greater than zero.")

    archive_path = settings.DATA_DIR / \
        f"{settings.PLAYER_GAME_NAME}_match_ids.json"
    archived_match_ids = _load_archived_match_ids(archive_path)

    bridge = RiotBridge()
    account_data = bridge.get_account_by_riot_id(
        settings.PLAYER_GAME_NAME,
        settings.PLAYER_TAG_LINE,
    )
    puuid = account_data.get("puuid")
    if not puuid:
        raise ValueError("Riot's account response does not contain a PUUID.")

    match_id_extractor = MatchExtractor(bridge)
    if full_rescan:
        scanned_match_ids = match_id_extractor.fetch_all_match_ids(puuid)
        archived_ids = set(archived_match_ids)
        discovered_match_ids = [
            match_id for match_id in scanned_match_ids if match_id not in archived_ids
        ]
    else:
        discovered_match_ids = match_id_extractor.fetch_new_match_ids(
            puuid, archived_match_ids
        )

    all_match_ids = match_id_extractor.merge_match_ids(
        discovered_match_ids,
        archived_match_ids,
    )
    if discovered_match_ids or not archive_path.exists():
        _write_match_id_archive(archive_path, all_match_ids)

    detail_extractor = DetailExtractor(bridge=bridge)
    oldest_pending_match_ids = detail_extractor.select_pending_match_ids(
        list(reversed(all_match_ids)), match_limit
    )
    if oldest_pending_match_ids:
        failed_match_count = detail_extractor.extract_and_save_batch(
            oldest_pending_match_ids
        )
    else:
        failed_match_count = 0

    return SyncResult(
        discovered_match_count=len(discovered_match_ids),
        archived_match_count=len(all_match_ids),
        selected_match_count=len(oldest_pending_match_ids),
        failed_match_count=failed_match_count,
        full_rescan=full_rescan,
    )


def rebuild_analysis_reports() -> int:
    match_rows = load_player_match_rows(
        settings.DATA_DIR / "raw" / "matches",
        settings.PLAYER_GAME_NAME,
        settings.PLAYER_TAG_LINE,
    )
    export_match_analysis(match_rows, settings.DATA_DIR / "processed")
    return len(match_rows)


def validate_local_data() -> dict:
    match_ids_path = settings.DATA_DIR / \
        f"{settings.PLAYER_GAME_NAME}_match_ids.json"
    archived_ids = _load_archived_match_ids(match_ids_path)
    match_directory = settings.DATA_DIR / "raw" / "matches"
    timeline_directory = settings.DATA_DIR / "raw" / "timelines"

    missing_match_ids = [
        match_id
        for match_id in archived_ids
        if not (match_directory / f"{match_id}.json").is_file()
    ]
    missing_timeline_ids = [
        match_id
        for match_id in archived_ids
        if not (timeline_directory / f"{match_id}_timeline.json").is_file()
    ]

    return {
        "archived_match_count": len(archived_ids),
        "match_file_count": len(list(match_directory.glob("*.json"))),
        "timeline_file_count": len(list(timeline_directory.glob("*_timeline.json"))),
        "missing_match_count": len(missing_match_ids),
        "missing_timeline_count": len(missing_timeline_ids),
    }

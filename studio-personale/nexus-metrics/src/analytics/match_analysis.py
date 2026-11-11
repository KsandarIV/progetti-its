import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


MATCH_COLUMNS = [
    "match_id",
    "played_at_utc",
    "calendar_month",
    "game_version",
    "queue_id",
    "game_mode",
    "duration_minutes",
    "champion",
    "team_position",
    "win",
    "kills",
    "deaths",
    "assists",
    "kda_ratio",
    "minions_killed",
    "neutral_minions_killed",
    "cs_per_minute",
    "champion_damage",
    "vision_score",
]
SUMMARY_COLUMNS = [
    "group_value",
    "games",
    "wins",
    "losses",
    "win_rate_pct",
    "avg_kills",
    "avg_deaths",
    "avg_assists",
    "kda_ratio",
    "avg_cs_per_minute",
    "avg_champion_damage",
    "avg_vision_score",
    "avg_duration_minutes",
]


def extract_player_match_row(
    match_data: Dict[str, Any], game_name: str, tag_line: str
) -> Dict[str, Any]:
    info = match_data.get("info")
    metadata = match_data.get("metadata")
    if not isinstance(info, dict) or not isinstance(metadata, dict):
        raise ValueError("Match response is missing metadata or info.")

    participants = info.get("participants")
    if not isinstance(participants, list):
        raise ValueError("Match response does not contain a participant list.")

    account_name = game_name.casefold()
    account_tag = tag_line.casefold()
    player_matches = [
        participant
        for participant in participants
        if str(participant.get("riotIdGameName") or "").casefold() == account_name
        and str(participant.get("riotIdTagline") or "").casefold() == account_tag
    ]
    if len(player_matches) != 1:
        raise ValueError(
            f"Expected exactly one account participant; found {len(player_matches)}."
        )

    player = player_matches[0]
    creation_time = info.get("gameCreation")
    duration_seconds = info.get("gameDuration")
    if not isinstance(creation_time, (int, float)):
        raise ValueError(
            "Match response is missing a valid game creation timestamp.")
    if not isinstance(duration_seconds, (int, float)) or duration_seconds <= 0:
        raise ValueError("Match response is missing a valid game duration.")

    played_at = datetime.fromtimestamp(
        creation_time / 1000, tz=timezone.utc
    )
    duration_minutes = duration_seconds / 60
    minions_killed = int(player.get("totalMinionsKilled", 0) or 0)
    neutral_minions_killed = int(player.get("neutralMinionsKilled", 0) or 0)
    kills = int(player.get("kills", 0) or 0)
    deaths = int(player.get("deaths", 0) or 0)
    assists = int(player.get("assists", 0) or 0)

    return {
        "match_id": metadata.get("matchId", ""),
        "played_at_utc": played_at.isoformat(),
        "calendar_month": played_at.strftime("%Y-%m"),
        "game_version": info.get("gameVersion", "unknown"),
        "queue_id": info.get("queueId", "unknown"),
        "game_mode": info.get("gameMode", "unknown"),
        "duration_minutes": round(duration_minutes, 2),
        "champion": player.get("championName", "unknown"),
        "team_position": player.get("teamPosition") or "UNKNOWN",
        "win": bool(player.get("win", False)),
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda_ratio": round((kills + assists) / deaths, 2) if deaths else None,
        "minions_killed": minions_killed,
        "neutral_minions_killed": neutral_minions_killed,
        "cs_per_minute": round(
            (minions_killed + neutral_minions_killed) / duration_minutes, 2
        ),
        "champion_damage": int(player.get("totalDamageDealtToChampions", 0) or 0),
        "vision_score": int(player.get("visionScore", 0) or 0),
    }


def load_player_match_rows(
    matches_directory: Path, game_name: str, tag_line: str
) -> List[Dict[str, Any]]:
    rows = []
    for match_path in sorted(matches_directory.glob("*.json")):
        try:
            match_data = json.loads(match_path.read_text(encoding="utf-8"))
            rows.append(extract_player_match_row(
                match_data, game_name, tag_line))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Could not read match file {match_path.name}.") from error
        except ValueError as error:
            raise ValueError(
                f"Invalid match file {match_path.name}: {error}") from error

    if not rows:
        raise ValueError(f"No match JSON files found in {matches_directory}.")
    return rows


def summarize_rows(
    rows: Iterable[Dict[str, Any]], group_by: Optional[str]
) -> List[Dict[str, Any]]:
    groups: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_value = row.get(group_by, "unknown") if group_by else "all"
        groups[group_value].append(row)

    summaries = []
    for group_value, group_rows in groups.items():
        games = len(group_rows)
        wins = sum(bool(row["win"]) for row in group_rows)
        total_deaths = sum(row["deaths"] for row in group_rows)
        total_kills = sum(row["kills"] for row in group_rows)
        total_assists = sum(row["assists"] for row in group_rows)
        summaries.append(
            {
                "group_value": group_value,
                "games": games,
                "wins": wins,
                "losses": games - wins,
                "win_rate_pct": round(wins * 100 / games, 2),
                "avg_kills": round(total_kills / games, 2),
                "avg_deaths": round(total_deaths / games, 2),
                "avg_assists": round(total_assists / games, 2),
                "kda_ratio": (
                    round((total_kills + total_assists) / total_deaths, 2)
                    if total_deaths
                    else None
                ),
                "avg_cs_per_minute": round(
                    sum(row["cs_per_minute"] for row in group_rows) / games, 2
                ),
                "avg_champion_damage": round(
                    sum(row["champion_damage"]
                        for row in group_rows) / games, 2
                ),
                "avg_vision_score": round(
                    sum(row["vision_score"] for row in group_rows) / games, 2
                ),
                "avg_duration_minutes": round(
                    sum(row["duration_minutes"]
                        for row in group_rows) / games, 2
                ),
            }
        )

    return sorted(summaries, key=lambda summary: str(summary["group_value"]))


def write_csv(
    output_path: Path, rows: Iterable[Dict[str, Any]], columns: List[str]
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_match_analysis(
    match_rows: List[Dict[str, Any]], output_directory: Path
) -> None:
    write_csv(output_directory / "matches.csv", match_rows, MATCH_COLUMNS)
    for group_by, filename in (
        ("calendar_month", "by_month.csv"),
        ("game_version", "by_patch.csv"),
        ("champion", "by_champion.csv"),
        ("team_position", "by_position.csv"),
        ("queue_id", "by_queue.csv"),
    ):
        write_csv(
            output_directory / filename,
            summarize_rows(match_rows, group_by),
            SUMMARY_COLUMNS,
        )

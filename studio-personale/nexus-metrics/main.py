import argparse
import logging

from src.core.exceptions import RateLimitExceededError, RiotAPIError
from src.services.match_workflows import synchronize_matches


def positive_integer(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "limit must be an integer.") from error

    if parsed_value < 1:
        raise argparse.ArgumentTypeError("limit must be greater than zero.")
    return parsed_value


def main(match_limit: int = 100, full_rescan: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
    )

    try:
        result = synchronize_matches(match_limit, full_rescan)
    except RateLimitExceededError:
        logging.error(
            "Extraction paused after repeated Riot rate limits. "
            "Wait before rerunning; completed files will be skipped."
        )
        raise SystemExit(1)
    except (RiotAPIError, RuntimeError, ValueError, OSError) as error:
        logging.error("Match synchronization failed: %s", error)
        raise SystemExit(1) from error

    print(
        f"Discovered {result.discovered_match_count} new matches; "
        f"{result.archived_match_count} unique IDs are archived."
    )
    if result.selected_match_count == 0:
        print("All available matches already have complete local files.")
    elif result.failed_match_count:
        print(
            f"Batch finished with {result.failed_match_count} failed matches. "
            "Rerun to retry; complete files will be skipped."
        )
    else:
        print(
            f"Batch extraction completed for {result.selected_match_count} matches."
        )


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(
        description="Synchronize and download available League of Legends matches."
    )
    argument_parser.add_argument(
        "--limit",
        type=positive_integer,
        default=100,
        help="Maximum number of pending matches to download (default: 100).",
    )
    argument_parser.add_argument(
        "--full-rescan",
        action="store_true",
        help="Scan all available match IDs for historical matches added retroactively.",
    )
    arguments = argument_parser.parse_args()
    main(arguments.limit, arguments.full_rescan)

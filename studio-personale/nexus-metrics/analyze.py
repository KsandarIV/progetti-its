import logging

from src.config import settings
from src.services.match_workflows import rebuild_analysis_reports


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
    )
    try:
        match_count = rebuild_analysis_reports()
    except ValueError as error:
        logging.error("Match analysis could not start: %s", error)
        raise SystemExit(1) from error

    print(f"Analyzed {match_count} matches.")
    print(f"CSV reports saved to {settings.DATA_DIR / 'processed'}.")


if __name__ == "__main__":
    main()

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    RIOT_API_KEY: str = os.getenv("RIOT_API_KEY", "")
    PLAYER_GAME_NAME: str = os.getenv("RIOT_GAME_NAME", "your_game_name")
    PLAYER_TAG_LINE: str = os.getenv("RIOT_TAG_LINE", "euw")
    REGION_ROUTING: str = "europe"
    PLATFORM_ROUTING: str = "euw1"

    # * — Riot API application limits —
    RATE_LIMIT_SHORT_CALLS: int = 10
    RATE_LIMIT_SHORT_PERIOD: int = 1
    RATE_LIMIT_LONG_CALLS: int = 90
    RATE_LIMIT_LONG_PERIOD: int = 120

    DATA_DIR: Path = PROJECT_ROOT / "data"


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

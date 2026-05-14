import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from src.utils import ensure_directory, safe_get

BASE_URL = "https://api-web.nhle.com/v1"


def http_get_json_with_retry(url: str, timeout: int = 30, retries: int = 3, backoff_sec: float = 1.0) -> dict:
    """Fetch JSON from URL with exponential backoff retry logic."""
    last_err: Optional[Exception] = None
    current_timeout = timeout

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=current_timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429,) or 500 <= r.status_code < 600:
                last_err = RuntimeError(f"HTTP {r.status_code} url={url}")
            else:
                r.raise_for_status()
        except (requests.RequestException, ValueError) as e:
            last_err = e

        if attempt < retries:
            wait_time = backoff_sec * attempt
            print(f"  Retry {attempt}/{retries} after {wait_time}s for {url}")
            time.sleep(wait_time)
            current_timeout = min(current_timeout * 2, 120)

    if last_err:
        print(f"Warning: failed to fetch {url}: {last_err}")
        return {}
    return {}


def parse_game_from_schedule(game: dict, day_date: str, ingested_at: str) -> Optional[dict]:
    """Parse a single game from /schedule/{date} response."""
    game_id = game.get("id")
    if game_id is None:
        return None

    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})
    score = game.get("score", {})
    outcome = game.get("gameOutcome", {})

    return {
        "game_id": int(game_id),
        "game_date": day_date,
        "season": game.get("season"),
        "game_type": game.get("gameType"),
        "venue": safe_get(game, "venue", "default"),
        "home_team_abbrev": home_team.get("abbrev"),
        "away_team_abbrev": away_team.get("abbrev"),
        "home_team_name": home_team.get("name"),
        "away_team_name": away_team.get("name"),
        "home_score": score.get("home") if isinstance(score, dict) else 0,
        "away_score": score.get("away") if isinstance(score, dict) else 0,
        "game_state": game.get("gameState"),
        "start_time_utc": game.get("startTimeUTC"),
        "source_date": day_date,
        "ingested_at": ingested_at,
    }


def extract_nhl_data(start_date: str, end_date: str, output_dir: str = "data/raw", sleep_sec: float = 0.1) -> tuple[str, int]:
    """
    Extract NHL game data from /schedule/{date} endpoint.
    
    Returns tuple of (local_file_path, row_count).
    """
    ensure_directory(output_dir)
    extracted_records: list[dict] = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    # Convert string dates to datetime for range iteration
    start_dt = datetime.fromisoformat(start_date).date()
    end_dt = datetime.fromisoformat(end_date).date()
    current_dt = start_dt

    while current_dt <= end_dt:
        current_date_str = current_dt.isoformat()
        print(f"Extracting NHL data for {current_date_str}")

        schedule_url = f"{BASE_URL}/schedule/{current_date_str}"
        schedule_response = http_get_json_with_retry(schedule_url)

        # Parse gameWeek structure from schedule endpoint
        game_count_today = 0
        for day_block in schedule_response.get("gameWeek", []):
            day_date = day_block.get("date")
            if not day_date:
                continue

            # Parse day_date to ensure it's within our range
            try:
                day_dt = datetime.fromisoformat(day_date).date()
            except (ValueError, TypeError):
                continue

            if day_dt < start_dt or day_dt > end_dt:
                continue

            for game in day_block.get("games", []):
                parsed = parse_game_from_schedule(game, day_date, ingested_at)
                if parsed:
                    extracted_records.append(parsed)
                    game_count_today += 1

        if game_count_today == 0:
            print(f"  No games found for {current_date_str}")
        else:
            print(f"  Found {game_count_today} games for {current_date_str}")

        time.sleep(sleep_sec)
        current_dt += timedelta(days=1)

    local_filename = f"nhl_games_{start_date}_{end_date}.jsonl"
    output_path = str(Path(output_dir) / local_filename)

    if extracted_records:
        df = pd.DataFrame(extracted_records)
        df.to_json(output_path, orient="records", lines=True, date_format="iso")
    else:
        print("No records extracted. Writing an empty JSONL file.")
        Path(output_path).write_text("")

    print(f"Extracted {len(extracted_records)} rows to {output_path}")
    return output_path, len(extracted_records)

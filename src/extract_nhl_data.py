import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from src.utils import ensure_directory, safe_get

BASE_URL = "https://api-web.nhle.com/v1"


def http_get_json_with_retry(url: str, timeout: int = 30, retries: int = 3, backoff_sec: float = 1.0) -> tuple[dict, int]:
    """Fetch JSON from URL with exponential backoff retry logic. Returns (data, status_code)."""
    last_err: Optional[Exception] = None
    current_timeout = timeout
    status_code = 0

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=current_timeout)
            status_code = r.status_code
            if r.status_code == 200:
                return r.json(), 200
            if r.status_code in (429,) or 500 <= r.status_code < 600:
                last_err = RuntimeError(f"HTTP {r.status_code}")
            else:
                r.raise_for_status()
        except (requests.RequestException, ValueError) as e:
            last_err = e

        if attempt < retries:
            wait_time = backoff_sec * attempt
            print(f"    Retry {attempt}/{retries} after {wait_time}s...")
            time.sleep(wait_time)
            current_timeout = min(current_timeout * 2, 120)

    if last_err:
        print(f"    Error: {last_err}")
    return {}, status_code


def extract_team_name(team: dict) -> Optional[str]:
    """Extract team name from commonName.default or placeName.default."""
    common_name = safe_get(team, "commonName", "default")
    if common_name:
        return common_name
    place_name = safe_get(team, "placeName", "default")
    return place_name


def parse_game_from_score(game: dict, ingested_at: str) -> Optional[dict]:
    """Parse a single game from /score/{date} response."""
    game_id = game.get("id")
    if game_id is None:
        return None

    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})

    home_score = home_team.get("score")
    away_score = away_team.get("score")
    
    # Ensure scores are int or None, not string
    if home_score is not None:
        try:
            home_score = int(home_score)
        except (ValueError, TypeError):
            home_score = None
    
    if away_score is not None:
        try:
            away_score = int(away_score)
        except (ValueError, TypeError):
            away_score = None

    # Parse game_date from gameDate field
    game_date = game.get("gameDate", "").split("T")[0]  # Take date part only

    return {
        "game_id": int(game_id),
        "game_date": game_date,
        "season": game.get("season"),
        "game_type": game.get("gameType"),
        "venue": safe_get(game, "venue", "default"),
        "home_team_abbrev": home_team.get("abbrev"),
        "away_team_abbrev": away_team.get("abbrev"),
        "home_team_name": extract_team_name(home_team),
        "away_team_name": extract_team_name(away_team),
        "home_score": home_score,
        "away_score": away_score,
        "game_state": game.get("gameState"),
        "start_time_utc": game.get("startTimeUTC"),
        "source_date": game_date,
        "ingested_at": ingested_at,
    }


def parse_game_from_schedule_fallback(game: dict, day_date: str, ingested_at: str) -> Optional[dict]:
    """Parse a single game from /schedule/{date} endpoint (fallback only)."""
    game_id = game.get("id")
    if game_id is None:
        return None

    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})

    return {
        "game_id": int(game_id),
        "game_date": day_date,
        "season": game.get("season"),
        "game_type": game.get("gameType"),
        "venue": safe_get(game, "venue", "default"),
        "home_team_abbrev": home_team.get("abbrev"),
        "away_team_abbrev": away_team.get("abbrev"),
        "home_team_name": extract_team_name(home_team),
        "away_team_name": extract_team_name(away_team),
        "home_score": None,  # schedule endpoint doesn't have scores
        "away_score": None,
        "game_state": game.get("gameState"),
        "start_time_utc": game.get("startTimeUTC"),
        "source_date": day_date,
        "ingested_at": ingested_at,
    }


def extract_nhl_data(start_date: str, end_date: str, output_dir: str = "data/raw", sleep_sec: float = 0.1) -> tuple[str, int]:
    """
    Extract NHL game data from /score/{date} endpoint (primary) with /schedule as fallback.
    
    Returns tuple of (local_file_path, row_count).
    """
    ensure_directory(output_dir)
    extracted_records: dict[int, dict] = {}  # Use dict to deduplicate by game_id
    ingested_at = datetime.now(timezone.utc).isoformat()

    # Convert string dates to datetime for range iteration
    start_dt = datetime.fromisoformat(start_date).date()
    end_dt = datetime.fromisoformat(end_date).date()
    current_dt = start_dt

    while current_dt <= end_dt:
        current_date_str = current_dt.isoformat()
        print(f"\n[{current_date_str}] Extracting NHL game data")

        # Primary: Try /score/{date} endpoint for actual game scores
        score_url = f"{BASE_URL}/score/{current_date_str}"
        print(f"  Score API:    {score_url}")
        score_data, score_status = http_get_json_with_retry(score_url)
        
        games_from_score = []
        if score_status == 200:
            score_games = score_data.get("games", [])
            games_from_score = score_games
            print(f"  HTTP Status:  {score_status} OK")
            print(f"  Games found:  {len(games_from_score)}")
            
            for game in games_from_score:
                parsed = parse_game_from_score(game, ingested_at)
                if parsed:
                    extracted_records[parsed["game_id"]] = parsed
        else:
            print(f"  HTTP Status:  {score_status}")

        # Fallback: If score endpoint returned no games, try /schedule/{date}
        if not games_from_score:
            print(f"  Falling back to Schedule API...")
            schedule_url = f"{BASE_URL}/schedule/{current_date_str}"
            print(f"  Schedule API: {schedule_url}")
            schedule_data, schedule_status = http_get_json_with_retry(schedule_url)
            print(f"  HTTP Status:  {schedule_status}")

            if schedule_status == 200:
                # Try top-level games first (some endpoints have this)
                games_from_schedule = schedule_data.get("games", [])
                
                # If no top-level games, try gameWeek structure
                if not games_from_schedule:
                    for day_block in schedule_data.get("gameWeek", []):
                        day_date = day_block.get("date")
                        if not day_date:
                            continue
                        try:
                            day_dt = datetime.fromisoformat(day_date).date()
                        except (ValueError, TypeError):
                            continue
                        if day_dt == current_dt:
                            games_from_schedule.extend(day_block.get("games", []))
                
                print(f"  Games found:  {len(games_from_schedule)}")
                
                for game in games_from_schedule:
                    parsed = parse_game_from_schedule_fallback(game, current_date_str, ingested_at)
                    if parsed and parsed["game_id"] not in extracted_records:
                        extracted_records[parsed["game_id"]] = parsed

        time.sleep(sleep_sec)
        current_dt += timedelta(days=1)

    # Convert deduplicated dict back to list
    records_list = list(extracted_records.values())

    local_filename = f"nhl_games_{start_date}_{end_date}.jsonl"
    output_path = str(Path(output_dir) / local_filename)

    if records_list:
        df = pd.DataFrame(records_list)
        df.to_json(output_path, orient="records", lines=True, date_format="iso")
    else:
        print("\nNo records extracted. Writing an empty JSONL file.")
        Path(output_path).write_text("")

    print(f"\nExtraction complete: {len(records_list)} unique games to {output_path}")
    return output_path, len(records_list)

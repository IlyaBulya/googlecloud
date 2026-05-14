import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from src.utils import ensure_directory, safe_get

BASE_URL = "https://api-web.nhle.com/v1"


def http_get_json_with_retry(url: str, timeout: int = 30, retries: int = 3, backoff_sec: float = 1.0) -> tuple[dict, int]:
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
        except (requests.RequestException, ValueError) as exc:
            last_err = exc

        if attempt < retries:
            wait_time = backoff_sec * attempt
            print(f"    Retry {attempt}/{retries} after {wait_time}s...")
            time.sleep(wait_time)
            current_timeout = min(current_timeout * 2, 120)

    if last_err:
        print(f"    Error: {last_err}")
    return {}, status_code


def extract_team_name(team: dict) -> Optional[str]:
    common_name = safe_get(team, "commonName", "default")
    if common_name:
        return common_name
    return safe_get(team, "placeName", "default")


def parse_upcoming_game(game: dict, source_date: str, ingested_at: str) -> Optional[dict]:
    game_id = game.get("id")
    if game_id is None:
        return None

    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})
    game_date = game.get("gameDate", source_date)
    if isinstance(game_date, str) and "T" in game_date:
        game_date = game_date.split("T")[0]

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
        "home_score": None,
        "away_score": None,
        "game_state": game.get("gameState"),
        "start_time_utc": game.get("startTimeUTC"),
        "source_date": source_date,
        "ingested_at": ingested_at,
    }


def extract_upcoming_games(upcoming_date: str, output_dir: str = "data/raw") -> tuple[str, int]:
    ensure_directory(output_dir)
    ingested_at = datetime.now(timezone.utc).isoformat()
    output_path = str(Path(output_dir) / f"upcoming_games_{upcoming_date}.jsonl")
    endpoint_url = f"{BASE_URL}/schedule/{upcoming_date}"

    print(f"Extracting upcoming games for {upcoming_date}")
    print(f"  Schedule API: {endpoint_url}")

    schedule_data, status_code = http_get_json_with_retry(endpoint_url)
    print(f"  HTTP Status: {status_code}")

    games = schedule_data.get("games", [])
    if not games:
        for day_block in schedule_data.get("gameWeek", []):
            day_date = day_block.get("date")
            if not day_date:
                continue
            try:
                datetime.fromisoformat(day_date)
            except (TypeError, ValueError):
                continue
            games.extend(day_block.get("games", []))

    if not games:
        for date_block in schedule_data.get("dates", []):
            games.extend(date_block.get("games", []))

    print(f"  Games found: {len(games)}")

    records: dict[int, dict] = {}
    for game in games:
        parsed = parse_upcoming_game(game, upcoming_date, ingested_at)
        if parsed:
            records[parsed["game_id"]] = parsed

    with open(output_path, "w", encoding="utf-8") as writer:
        for record in records.values():
            writer.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"  Output file: {output_path}")
    return output_path, len(records)
